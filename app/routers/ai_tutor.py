import asyncio
import json
import logging
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatConversationCreate,
    ChatConversationResponse, ChatConversationWithMessages,
    ChatMessageResponse
)
from app.models.chat import ChatConversation, ChatMessage
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service
from app.services.web_research_service import web_research_service

logger = logging.getLogger(__name__)

router = APIRouter()


@dataclass(frozen=True, slots=True)
class TutorProfile:
    """Runtime behavior selected for one tutor response."""

    name: str
    model: Optional[str] = None
    system_behavior: str = ""


class TutorRuntimeConfig:
    """Reload JSON configuration when its file changes, without a restart."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._modified_at: Optional[int] = None
        self._profiles: dict[str, TutorProfile] = {"default": TutorProfile("default")}
        self._default_profile = "default"

    def get_profile(self, name: str) -> TutorProfile:
        self._reload_if_changed()
        return self._profiles.get(name, self._profiles[self._default_profile])

    def _reload_if_changed(self) -> None:
        try:
            modified_at = self._path.stat().st_mtime_ns
        except FileNotFoundError:
            return
        if modified_at == self._modified_at:
            return
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
            profiles = self._parse_profiles(payload)
        except (OSError, ValueError, TypeError) as error:
            logger.warning("Keeping the previous AI tutor configuration: %s", error)
            return
        self._profiles = profiles
        self._default_profile = payload.get("default_profile", "default")
        if self._default_profile not in profiles:
            self._default_profile = "default"
        self._modified_at = modified_at
        logger.info("Reloaded AI tutor configuration from %s", self._path)

    @staticmethod
    def _parse_profiles(payload: Mapping[str, Any]) -> dict[str, TutorProfile]:
        raw_profiles = payload.get("profiles", {})
        if not isinstance(raw_profiles, Mapping):
            raise ValueError("profiles must be an object")
        profiles = {"default": TutorProfile("default")}
        for name, values in raw_profiles.items():
            if not isinstance(name, str) or not isinstance(values, Mapping):
                raise ValueError("each profile must have a string name and object settings")
            profiles[name] = TutorProfile(
                name=name,
                model=values.get("model") or None,
                system_behavior=str(values.get("system_behavior", "")),
            )
        return profiles


ProfileSelector = Callable[[str, str], Optional[str]]


class TutorProfileRouter:
    """Select a profile through small, replaceable context callbacks."""

    def __init__(self, config: TutorRuntimeConfig, selectors: List[ProfileSelector]) -> None:
        self._config = config
        self._selectors = selectors

    def select(self, question: str, explanation_style: str) -> TutorProfile:
        for selector in self._selectors:
            profile_name = selector(question, explanation_style)
            if profile_name:
                return self._config.get_profile(profile_name)
        return self._config.get_profile("default")


def _technical_profile(_: str, explanation_style: str) -> Optional[str]:
    return "technical" if explanation_style.lower() == "technical" else None


def _concise_profile(question: str, _: str) -> Optional[str]:
    concise_terms = ("brief", "short answer", "concise", "summarize")
    return "concise" if any(term in question.lower() for term in concise_terms) else None


class GreetingResponder:
    """Handle short greetings instantly without unnecessary retrieval."""

    _pattern = re.compile(
        r"^\s*(?:hi|hello|hey|yo|sup|what'?s up|paaji|brother)(?:\s+(?:there|bro|brother|buddy|assistant))?[!?.\s]*$",
        re.IGNORECASE,
    )
    _how_are_you_pattern = re.compile(
        r"^\s*how are you(?: doing)?(?:[,\s]+(?:bro|brother|paaji|buddy))?[!?.\s]*$",
        re.IGNORECASE,
    )

    def respond(self, message: str) -> Optional[Dict[str, Any]]:
        if self._how_are_you_pattern.match(message):
            return {"answer": "I'm doing well, thanks for asking! How can I help?", "sources": []}
        if not self._pattern.match(message):
            return None
        if "bro" in message.lower() or message.lower().strip().startswith(("yo", "sup", "paaji")):
            answer = "Hey, brother! What can I help with?"
        elif message.lower().strip().startswith("hey"):
            answer = "Hey! Good to chat with you. What do you need help with?"
        else:
            answer = "Hello! How can I help you today?"
        return {"answer": answer, "sources": []}


class AsyncTutorCoordinator:
    """Keep blocking retrieval and model work out of the FastAPI event loop."""

    def __init__(self, profile_router: TutorProfileRouter, max_concurrent_requests: int = 8) -> None:
        self._profile_router = profile_router
        self._greeting_responder = GreetingResponder()
        self._semaphore = asyncio.Semaphore(max_concurrent_requests)

    @staticmethod
    def _wants_web_research(question: str) -> bool:
        return bool(
            re.search(
                r"\b(?:search|look|find)\b.{0,24}\b(?:web|online|internet)\b"
                r"|\bweb\s+search\b",
                question,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _search_context(
        user_id: int, question: str, document_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Use a thread-local SQLAlchemy session for blocking retrieval work."""
        with SessionLocal() as retrieval_db:
            return rag_service.search_similar_chunks(
                user_id, question, top_k=5, db=retrieval_db, document_id=document_id
            )

    async def generate_response(
        self,
        *,
        user_id: int,
        question: str,
        explanation_style: Any,
        conversation_history: List[Dict[str, str]],
        document_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        greeting = self._greeting_responder.respond(question)
        if greeting is not None:
            return greeting
        style_value = getattr(explanation_style, "value", str(explanation_style))
        profile = await asyncio.to_thread(self._profile_router.select, question, style_value)
        async with self._semaphore:
            chunks = []
            if document_id is not None:
                chunks = await asyncio.to_thread(
                    self._search_context, user_id, question, document_id
                )
            if not chunks and self._wants_web_research(question):
                chunks = await asyncio.to_thread(web_research_service.search, question)
            return await asyncio.to_thread(
                ai_service.generate_chat_response,
                question,
                chunks,
                explanation_style,
                conversation_history,
                model=profile.model,
                system_behavior=profile.system_behavior,
            )


_runtime_config = TutorRuntimeConfig(Path(__file__).with_name("ai_tutor_config.json"))
_profile_router = TutorProfileRouter(_runtime_config, [_technical_profile, _concise_profile])
tutor_coordinator = AsyncTutorCoordinator(_profile_router)


# WebSocket Connection Manager for real-time chat
class ConnectionManager:
    """Manage WebSocket connections for real-time chat."""
    
    def __init__(self):
        # Store active connections: {conversation_id: [websocket, user_id, ...]}
        self.active_connections: Dict[int, List] = {}
        self.user_conversations: Dict[int, List[int]] = {}  # user_id -> [conversation_ids]
    
    async def connect(self, websocket: WebSocket, conversation_id: int, user_id: int):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        
        self.active_connections[conversation_id].append({
            "websocket": websocket,
            "user_id": user_id,
            "connected_at": datetime.now()
        })
        
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = []
        
        if conversation_id not in self.user_conversations[user_id]:
            self.user_conversations[user_id].append(conversation_id)
        
        logger.info(f"User {user_id} connected to conversation {conversation_id}")
    
    def disconnect(self, conversation_id: int, user_id: int):
        """Unregister a WebSocket connection."""
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id] = [
                conn for conn in self.active_connections[conversation_id]
                if conn["user_id"] != user_id
            ]
            
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        
        logger.info(f"User {user_id} disconnected from conversation {conversation_id}")
    
    async def broadcast_to_conversation(self, conversation_id: int, message: dict):
        """Send message to all connected clients in a conversation."""
        if conversation_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection["websocket"].send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[conversation_id].remove(conn)
    
    async def broadcast_typing(self, conversation_id: int, user_id: int, is_typing: bool):
        """Broadcast typing status."""
        message = {
            "type": "typing",
            "user_id": user_id,
            "is_typing": is_typing,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_conversation(conversation_id, message)
    
    async def broadcast_message(self, conversation_id: int, message_data: dict):
        """Broadcast a new message to all connected clients."""
        message_data["timestamp"] = datetime.now().isoformat()
        await self.broadcast_to_conversation(conversation_id, message_data)
    
    def get_active_users(self, conversation_id: int) -> List[int]:
        """Get list of active user IDs in a conversation."""
        if conversation_id in self.active_connections:
            return [conn["user_id"] for conn in self.active_connections[conversation_id]]
        return []
    
    def is_user_online(self, user_id: int) -> bool:
        """Check if user has any active connections."""
        return any(
            any(conn["user_id"] == user_id for conn in conns)
            for conns in self.active_connections.values()
        )


# Global connection manager
manager = ConnectionManager()


# ==================== WebSocket Endpoints for Real-time Chat ====================

@router.websocket("/ws/chat/{conversation_id}/{token}")
async def websocket_chat_endpoint(websocket: WebSocket, conversation_id: int, token: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time AI tutor chat.
    
    Connect to: ws://127.0.0.1:8000/api/ai/ws/chat/{conversation_id}/{access_token}
    
    Message formats:
    - Send message: {"type": "message", "content": "your message"}
    - Start typing: {"type": "typing_start"}
    - Stop typing: {"type": "typing_stop"}
    - Get online users: {"type": "get_users"}
    """
    
    # Authenticate user from token
    from app.utils.security import decode_access_token
    
    try:
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        
        user_id = int(payload["sub"])
        current_user = db.query(User).filter(User.id == user_id).first()
        
        if not current_user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
            return
        
        # Verify user owns the conversation
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user_id
        ).first()
        
        if not conversation:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Conversation not found")
            return
        
        # Accept connection
        await manager.connect(websocket, conversation_id, user_id)
        
        # Notify others that user is online
        await manager.broadcast_to_conversation(conversation_id, {
            "type": "user_online",
            "user_id": user_id,
            "full_name": current_user.full_name,
            "active_users": manager.get_active_users(conversation_id),
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            while True:
                data = await websocket.receive_json()
                message_type = data.get("type", "message")
                
                if message_type == "message":
                    # Handle chat message
                    content = data.get("content", "").strip()
                    
                    if not content:
                        await websocket.send_json({"type": "error", "message": "Empty message"})
                        continue
                    
                    # Save user message to database
                    user_message = ChatMessage(
                        conversation_id=conversation_id,
                        role="user",
                        content=content
                    )
                    db.add(user_message)
                    db.commit()
                    db.refresh(user_message)
                    
                    # Broadcast user message to all connected clients
                    await manager.broadcast_message(conversation_id, {
                        "type": "message",
                        "role": "user",
                        "content": content,
                        "user_id": user_id,
                        "full_name": current_user.full_name,
                        "message_id": user_message.id
                    })
                    
                    # Generate AI response
                    try:
                        # Get conversation history
                        history = db.query(ChatMessage).filter(
                            ChatMessage.conversation_id == conversation_id
                        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
                        
                        history_messages = [
                            {"role": msg.role, "content": msg.content}
                            for msg in reversed(history[:-1])
                        ]
                        
                        # Search relevant chunks
                        raw_document_id = data.get("document_id", conversation.document_id)
                        if raw_document_id in ("", None):
                            selected_document_id = None
                        elif isinstance(raw_document_id, (int, str)) and str(raw_document_id).isdecimal():
                            selected_document_id = int(raw_document_id)
                        else:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Invalid selected document.",
                            })
                            continue

                        ai_response = await tutor_coordinator.generate_response(
                            user_id=user_id,
                            question=content,
                            explanation_style=current_user.explanation_style,
                            conversation_history=history_messages,
                            document_id=selected_document_id,
                        )
                        
                        # Save AI message
                        sources_json = json.dumps(ai_response.get('sources', []))
                        assistant_message = ChatMessage(
                            conversation_id=conversation_id,
                            role="assistant",
                            content=ai_response['answer'],
                            sources=sources_json
                        )
                        db.add(assistant_message)
                        db.commit()
                        db.refresh(assistant_message)
                        
                        # Broadcast AI response
                        await manager.broadcast_message(conversation_id, {
                            "type": "message",
                            "role": "assistant",
                            "content": ai_response['answer'],
                            "sources": ai_response.get('sources', []),
                            "message_id": assistant_message.id
                        })
                        
                    except Exception as e:
                        logger.error(f"Error generating AI response: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to generate AI response: {str(e)}"
                        })
                
                elif message_type == "typing_start":
                    # Notify others that user is typing
                    await manager.broadcast_typing(conversation_id, user_id, True)
                
                elif message_type == "typing_stop":
                    # Notify others that user stopped typing
                    await manager.broadcast_typing(conversation_id, user_id, False)
                
                elif message_type == "get_users":
                    # Send list of active users
                    active_users = manager.get_active_users(conversation_id)
                    await websocket.send_json({
                        "type": "active_users",
                        "users": active_users,
                        "count": len(active_users)
                    })
                
                else:
                    await websocket.send_json({"type": "error", "message": f"Unknown message type: {message_type}"})
        
        except WebSocketDisconnect:
            manager.disconnect(conversation_id, user_id)
            
            # Notify others that user is offline
            await manager.broadcast_to_conversation(conversation_id, {
                "type": "user_offline",
                "user_id": user_id,
                "full_name": current_user.full_name,
                "active_users": manager.get_active_users(conversation_id),
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"WebSocket disconnect: conversation {conversation_id}, user {user_id}")
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            manager.disconnect(conversation_id, user_id)
    
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=status.WS_1011_SERVER_ERROR, reason="Authentication failed")


@router.get("/online-status/{user_id}")
async def get_user_online_status(user_id: int):
    """Check if a user is currently online."""
    return {
        "user_id": user_id,
        "is_online": manager.is_user_online(user_id),
        "active_conversations": manager.user_conversations.get(user_id, [])
    }


@router.get("/active-conversations")
async def get_active_conversations(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of conversations with active connections."""
    active_convs = []
    for conv_id, connections in manager.active_connections.items():
        if any(conn["user_id"] == current_user.id for conn in connections):
            active_convs.append({
                "conversation_id": conv_id,
                "active_users": manager.get_active_users(conv_id),
                "user_count": len(manager.get_active_users(conv_id))
            })
    return {"active_conversations": active_convs}


# ==================== REST API Endpoints (for backward compatibility) ====================

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message to the AI tutor and get a response."""
    
    # Get or create conversation
    if chat_request.conversation_id:
        conversation = db.query(ChatConversation).filter(
            ChatConversation.id == chat_request.conversation_id,
            ChatConversation.user_id == current_user.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = ChatConversation(
            user_id=current_user.id,
            title=chat_request.message[:50] + "..." if len(chat_request.message) > 50 else chat_request.message,
            subject_id=chat_request.subject_id,
            topic_id=chat_request.topic_id,
            document_id=chat_request.document_id
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    # Save user message
    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=chat_request.message
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # Get conversation history (last 10 messages)
    history = db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation.id
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()
    
    history_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(history[:-1])  # Exclude the current message
    ]
    
    try:
        ai_response = await tutor_coordinator.generate_response(
            user_id=current_user.id,
            question=chat_request.message,
            explanation_style=current_user.explanation_style,
            conversation_history=history_messages,
            document_id=chat_request.document_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI response: {str(e)}"
        )
    
    # Save AI message
    sources_json = json.dumps(ai_response['sources'])
    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_response['answer'],
        sources=sources_json
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    
    # Broadcast messages to WebSocket clients for real-time updates
    await manager.broadcast_message(conversation.id, {
        "type": "message",
        "role": "user",
        "content": chat_request.message,
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "message_id": user_message.id
    })
    
    await manager.broadcast_message(conversation.id, {
        "type": "message",
        "role": "assistant",
        "content": ai_response['answer'],
        "sources": ai_response['sources'],
        "message_id": assistant_message.id
    })
    
    # Update conversation timestamp
    db.commit()
    
    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        answer=ai_response['answer'],
        sources=ai_response['sources']
    )


@router.get("/conversations", response_model=List[ChatConversationResponse])
async def get_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all conversations for the current user."""
    conversations = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.id
    ).order_by(ChatConversation.updated_at.desc()).all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ChatConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation with all messages."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation."""
    conversation = db.query(ChatConversation).filter(
        ChatConversation.id == conversation_id,
        ChatConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    return None


@router.post("/conversations", response_model=ChatConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ChatConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    conversation = ChatConversation(
        user_id=current_user.id,
        **conversation_data.model_dump()
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

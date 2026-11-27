from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    document_id: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    response: str
    sources: Optional[List[Dict[str, Any]]] = None


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    subject_id: Optional[int]
    topic_id: Optional[int]
    document_id: Optional[int]
    created_at: str
    updated_at: str
    messages: List[ChatMessage]

    class Config:
        from_attributes = True


class AIPromptRequest(BaseModel):
    prompt: str
    context: Optional[str] = None
    document_id: Optional[int] = None
    topic: Optional[str] = None


class AIResponse(BaseModel):
    response: str
    sources: Optional[List[Dict[str, Any]]] = None

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessageBase(BaseModel):
    role: str  # user, assistant
    content: str
    sources: Optional[str] = None  # JSON string of sources


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessageResponse(ChatMessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversationBase(BaseModel):
    title: Optional[str] = None
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    document_id: Optional[int] = None


class ChatConversationCreate(ChatConversationBase):
    pass


class ChatConversationResponse(ChatConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ChatConversationWithMessages(ChatConversationResponse):
    messages: List[ChatMessageResponse]


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    subject_id: Optional[int] = None
    topic_id: Optional[int] = None
    document_id: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    sources: List[Dict[str, Any]]
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.document import ProcessingStatus


class DocumentBase(BaseModel):
    original_filename: str
    subject_id: Optional[int] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(BaseModel):
    id: int
    original_filename: str
    file_type: str
    file_size: int
    user_id: int
    subject_id: Optional[int]
    subject_name: Optional[str] = None
    upload_date: datetime
    number_of_pages: Optional[int]
    processing_status: ProcessingStatus
    processing_error: Optional[str]

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_text: str
    page_number: Optional[int]
    subject: Optional[str]
    topic: Optional[str]
    chunk_index: int

    class Config:
        from_attributes = True
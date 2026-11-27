import os
import logging
import pypdf  # pypdf instead of PyMuPDF
from docx import Document as DocxDocument
from typing import Optional, Tuple
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentChunk, ProcessingStatus
from app.models.subject import Subject
from app.schemas.document import DocumentCreate
from app.config import settings
from app.services.rag_service import rag_service
from app.services.subject_recognition import detect_subject
from app.utils.helpers import (
    ensure_upload_dir, get_file_extension, is_allowed_file_type
)
from app.utils.chunking import clean_text, chunk_text_by_tokens

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert to bytes
logger = logging.getLogger(__name__)


def validate_file_upload(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    if not is_allowed_file_type(file.filename, ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF, DOCX, and TXT files are supported"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
        )


def extract_text_from_pdf(file_path: str) -> Tuple[list, int]:
    """Extract text from PDF file with page numbers."""
    import pypdf
    
    text_content = []
    
    with open(file_path, 'rb') as file:
        pdf_reader = pypdf.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        
        for page_num in range(total_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            if text.strip():
                text_content.append({
                    'page': page_num + 1,
                    'text': text
                })
    
    return text_content, total_pages


def extract_text_from_docx(file_path: str) -> Tuple[str, int]:
    """Extract text from DOCX file."""
    doc = DocxDocument(file_path)
    text_content = []
    
    for para in doc.paragraphs:
        if para.text.strip():
            text_content.append({
                'page': None,  # DOCX doesn't have page numbers
                'text': para.text
            })
    
    return text_content, 1  # Approximate page count


def extract_text_from_txt(file_path: str) -> Tuple[str, int]:
    """Extract text from TXT file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    return [{'page': None, 'text': text}], 1


def extract_text_by_file_type(file_path: str, file_type: str) -> Tuple[list, int]:
    """Extract text based on file type."""
    file_type = file_type.lower()
    
    if file_type == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_type == '.docx':
        return extract_text_from_docx(file_path)
    elif file_type == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_type}"
        )


def create_document_record(
    db: Session,
    user_id: int,
    filename: str,
    file_path: str,
    file_size: int,
    subject_id: Optional[int] = None
) -> Document:
    """Create a document record in the database."""
    file_type = get_file_extension(filename)
    
    db_document = Document(
        original_filename=filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        user_id=user_id,
        subject_id=subject_id,
        processing_status=ProcessingStatus.UPLOADING
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document


def process_document(
    db: Session,
    document: Document,
    subject_name: Optional[str] = None
) -> Document:
    """Process document: extract text, chunk, and save to database."""
    try:
        # Update status to processing
        document.processing_status = ProcessingStatus.PROCESSING
        db.commit()
        
        # Extract text
        text_content, num_pages = extract_text_by_file_type(
            document.file_path,
            document.file_type
        )

        if document.subject_id is None and not subject_name:
            document_text = "\n".join(item["text"] for item in text_content)
            detected_name = detect_subject(document_text, document.original_filename)
            if detected_name:
                subject = db.query(Subject).filter(
                    Subject.user_id == document.user_id,
                    Subject.name.ilike(detected_name),
                ).first()
                if subject is None:
                    subject = Subject(
                        name=detected_name,
                        description="Automatically identified from uploaded study material.",
                        user_id=document.user_id,
                    )
                    db.add(subject)
                    db.flush()
                document.subject_id = subject.id
                subject_name = subject.name
                db.commit()
        elif document.subject_id is not None and not subject_name:
            subject = db.query(Subject).filter(Subject.id == document.subject_id).first()
            subject_name = subject.name if subject else None
        
        document.number_of_pages = num_pages
        document.processing_status = ProcessingStatus.CHUNKING
        db.commit()
        
        # Process chunks
        all_chunks = []
        chunk_index = 0
        
        for content in text_content:
            cleaned_text = clean_text(content['text'])
            if not cleaned_text:
                continue
            
            # Chunk the text
            chunks = chunk_text_by_tokens(cleaned_text)
            
            for chunk_text in chunks:
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_text=chunk_text,
                    page_number=content['page'],
                    subject=subject_name,
                    chunk_index=chunk_index
                )
                db.add(chunk)
                all_chunks.append(chunk)
                chunk_index += 1
        
        db.commit()

        # Keep the searchable index in sync for generative answers from uploads.
        if settings.ai_configured and all_chunks:
            document.processing_status = ProcessingStatus.GENERATING_EMBEDDINGS
            db.commit()
            try:
                rag_service.process_document_for_rag(db, document)
            except Exception as embedding_error:
                logger.warning(
                    "Embedding generation failed; document will remain usable with keyword search: %s",
                    embedding_error,
                )
        
        # Update status to ready
        document.processing_status = ProcessingStatus.READY
        db.commit()
        db.refresh(document)
        
        return document
        
    except Exception as e:
        # Update status to failed
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}"
        )


def save_uploaded_file(file: UploadFile, user_id: int) -> str:
    """Save uploaded file to disk."""
    ensure_upload_dir(settings.UPLOAD_DIR)
    
    # Create user-specific directory
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = get_file_extension(file.filename)
    safe_filename = f"{user_id}_{hash(file.filename)}{file_extension}"
    file_path = os.path.join(user_upload_dir, safe_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return file_path


def get_user_documents(db: Session, user_id: int, subject_id: Optional[int] = None):
    """Get all documents for a user, optionally filtered by subject."""
    query = db.query(Document).filter(Document.user_id == user_id)
    
    if subject_id:
        query = query.filter(Document.subject_id == subject_id)
    
    return query.order_by(Document.upload_date.desc()).all()


def get_document_by_id(db: Session, document_id: int, user_id: int) -> Document:
    """Get a document by ID, ensuring it belongs to the user."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document


def delete_document(db: Session, document: Document) -> None:
    """Delete a document and its file."""
    # Delete file from disk
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete from database (cascade will handle chunks)
    db.delete(document)
    db.commit()

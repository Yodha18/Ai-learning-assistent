from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentChunkResponse
from app.models.document import Document
from app.models.user import User
from app.models.subject import Subject
from app.routers.auth import get_current_active_user
from app.services.document_service import (
    validate_file_upload,
    save_uploaded_file,
    create_document_record,
    process_document,
    get_user_documents,
    get_document_by_id,
    delete_document
)

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    subject_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process a document."""
    # Validate file
    validate_file_upload(file)
    
    # Verify subject if provided
    if subject_id:
        subject = db.query(Subject).filter(
            Subject.id == subject_id,
            Subject.user_id == current_user.id
        ).first()
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
    
    # Save file
    file_path = save_uploaded_file(file, current_user.id)
    
    # Get file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    # Create document record
    document = create_document_record(
        db,
        current_user.id,
        file.filename,
        file_path,
        file_size,
        subject_id
    )
    
    # Get subject name for chunks
    subject_name = subject.name if subject_id else None
    
    # Process document (extract text, chunk, etc.)
    try:
        document = process_document(db, document, subject_name)
    except Exception as e:
        # Document processing failed, record is already updated with error
        raise e
    
    return document


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    subject_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all documents for the current user, optionally filtered by subject."""
    documents = get_user_documents(db, current_user.id, subject_id)
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific document."""
    document = get_document_by_id(db, document_id, current_user.id)
    return document


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chunks for a document."""
    document = get_document_by_id(db, document_id, current_user.id)
    return document.chunks


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_route(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a document."""
    document = get_document_by_id(db, document_id, current_user.id)
    delete_document(db, document)
    return None
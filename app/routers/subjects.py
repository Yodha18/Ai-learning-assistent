from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectWithTopics, TopicCreate, TopicUpdate, TopicResponse
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User
from app.routers.auth import get_current_active_user

router = APIRouter()


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject_data: SubjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new subject for the current user."""
    db_subject = Subject(
        name=subject_data.name,
        description=subject_data.description,
        user_id=current_user.id
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


@router.get("/", response_model=List[SubjectResponse])
async def get_subjects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all subjects for the current user."""
    subjects = db.query(Subject).filter(Subject.user_id == current_user.id).all()
    return subjects


@router.get("/{subject_id}", response_model=SubjectWithTopics)
async def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific subject with its topics."""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    subject_data: SubjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a subject."""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    for field, value in subject_data.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a subject."""
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    db.delete(subject)
    db.commit()
    return None


# Topic endpoints
@router.post("/{subject_id}/topics", response_model=TopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    subject_id: int,
    topic_data: TopicCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new topic under a subject."""
    # Verify subject belongs to user
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    db_topic = Topic(
        name=topic_data.name,
        description=topic_data.description,
        difficulty=topic_data.difficulty,
        subject_id=subject_id
    )
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


@router.get("/{subject_id}/topics", response_model=List[TopicResponse])
async def get_topics(
    subject_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all topics for a subject."""
    # Verify subject belongs to user
    subject = db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
    return topics


@router.get("/topics/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific topic."""
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    return topic


@router.put("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: int,
    topic_data: TopicUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a topic."""
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    for field, value in topic_data.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a topic."""
    topic = db.query(Topic).join(Subject).filter(
        Topic.id == topic_id,
        Subject.user_id == current_user.id
    ).first()
    
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic not found"
        )
    
    db.delete(topic)
    db.commit()
    return None
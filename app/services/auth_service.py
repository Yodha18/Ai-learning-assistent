from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.user import User, LearningGoal, ExplanationStyle, Difficulty
from app.schemas.auth import UserCreate, UserLogin
from app.utils.security import verify_password, get_password_hash, create_access_token, validate_password_strength
from datetime import timedelta
from app.config import settings


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password strength
    is_valid, message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    
    # Convert string enums to actual enums
    try:
        learning_goal = LearningGoal(user_data.learning_goal) if user_data.learning_goal else LearningGoal.GENERAL
        preferred_difficulty = Difficulty(user_data.preferred_difficulty) if user_data.preferred_difficulty else Difficulty.MEDIUM
        explanation_style = ExplanationStyle(user_data.explanation_style) if user_data.explanation_style else ExplanationStyle.SIMPLE
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid enum value: {str(e)}"
        )
    
    db_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password,
        course=user_data.course,
        university=user_data.university,
        semester=user_data.semester,
        learning_goal=learning_goal,
        daily_study_time=user_data.daily_study_time or 120,
        preferred_difficulty=preferred_difficulty,
        explanation_style=explanation_style
    )
    
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        ) from error
    db.refresh(db_user)
    
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Authenticate a user and return the user if valid."""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return user


def create_user_token(user: User) -> str:
    """Create an access token for a user."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": str(user.id), "email": user.email}
    return create_access_token(token_data, access_token_expires)


def get_user_by_id(db: Session, user_id: int) -> User:
    """Get a user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_user_by_email(db: Session, email: str) -> User:
    """Get a user by email."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

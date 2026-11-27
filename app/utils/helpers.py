import os
from typing import Optional
from datetime import datetime


def ensure_upload_dir(upload_dir: str) -> None:
    """Ensure the upload directory exists."""
    os.makedirs(upload_dir, exist_ok=True)


def ensure_vector_store_dir(vector_store_dir: str) -> None:
    """Ensure the vector store directory exists."""
    os.makedirs(vector_store_dir, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename."""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file_type(filename: str, allowed_extensions: set) -> bool:
    """Check if a file type is allowed."""
    return get_file_extension(filename) in allowed_extensions


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: int) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    return f"{hours}h {remaining_minutes}m"


def calculate_streak(last_study_date: Optional[datetime]) -> int:
    """
    Calculate study streak based on last study date.
    Returns 0 if no study date or if streak is broken.
    """
    if not last_study_date:
        return 0
    
    today = datetime.now().date()
    last_date = last_study_date.date()
    
    if last_date == today:
        return 1
    
    delta = (today - last_date).days
    
    if delta == 1:
        return 1  # Streak continues, need history for full calculation
    elif delta > 1:
        return 0  # Streak broken
    
    return 0
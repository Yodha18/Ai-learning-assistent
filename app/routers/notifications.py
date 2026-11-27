from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.notification import Notification
from app.models.user import User
from app.routers.auth import get_current_active_user
from app.services.notification_service import (
    get_user_notifications,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification as delete_notification_service,
    get_unread_count
)

router = APIRouter()


@router.get("/")
async def get_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get notifications for the current user."""
    notifications = get_user_notifications(db, current_user.id, unread_only)
    return notifications


@router.get("/unread-count")
async def get_notifications_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications."""
    count = get_unread_count(db, current_user.id)
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a notification as read."""
    notification = mark_notification_read(db, notification_id, current_user.id)
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read."""
    count = mark_all_notifications_read(db, current_user.id)
    return {"marked_read": count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_route(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a notification."""
    success = delete_notification_service(db, notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return None
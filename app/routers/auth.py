import json
import secrets
import smtplib
from email.message import EmailMessage
from datetime import timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, TokenResponse
from app.schemas.user import UserResponse
from app.services.auth_service import create_user, authenticate_user, create_user_token, get_user_by_id
from app.utils.security import (
    decode_access_token,
    create_typed_token,
    decode_typed_token,
    get_password_hash,
    validate_password_strength,
)
from app.models.user import User
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = token or request.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user."""
    return current_user


async def get_optional_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    token = token or request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or payload.get("sub") is None:
        return None
    return get_user_by_id(db, int(payload["sub"]))


async def _request_data(request: Request) -> dict:
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            return await request.json()
        except json.JSONDecodeError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Please submit valid registration data.",
            ) from error
    form_data = await request.form()
    return dict(form_data)


def _validated_payload(schema: type[UserCreate] | type[UserLogin], data: dict):
    try:
        return schema.model_validate(data)
    except ValidationError as error:
        messages = [item["msg"] for item in error.errors()]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="; ".join(messages),
        ) from error


def _set_access_cookie(response: Response, access_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    is_form = not request.headers.get("content-type", "").startswith("application/json")
    user_data = _validated_payload(UserCreate, await _request_data(request))
    user = create_user(db, user_data)
    if is_form:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, response: Response, db: Session = Depends(get_db)):
    """Authenticate a user and return an access token."""
    is_form = not request.headers.get("content-type", "").startswith("application/json")
    user_credentials = _validated_payload(UserLogin, await _request_data(request))
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    access_token = create_user_token(user)
    if is_form:
        redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        _set_access_cookie(redirect, access_token)
        return redirect
    _set_access_cookie(response, access_token)
    return TokenResponse(access_token=access_token, user_id=user.id)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get the current user's profile."""
    return current_user


@router.post("/claim-full-access")
async def claim_full_access(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Grant the authenticated user full access to premium features."""
    current_user.full_access = True
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {
        "message": "Full access granted successfully.",
        "full_access": current_user.full_access,
        "user_id": current_user.id,
    }


@router.get("/google/start")
async def google_login_start():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured.",
        )

    state = create_typed_token(
        {"purpose": "google-login"},
        "google_oauth_state",
        timedelta(minutes=10),
    )
    params = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    })
    redirect = RedirectResponse(
        url=f"https://accounts.google.com/o/oauth2/v2/auth?{params}",
        status_code=status.HTTP_302_FOUND,
    )
    redirect.set_cookie(
        key="google_oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        max_age=600,
    )
    return redirect


@router.get("/google/callback")
async def google_login_callback(
    request: Request,
    response: Response,
    code: str = "",
    state: str = "",
    db: Session = Depends(get_db),
):
    saved_state = request.cookies.get("google_oauth_state")
    if not code or not state or not saved_state or state != saved_state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Google login request")
    payload = decode_typed_token(state, "google_oauth_state")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google login session expired")

    async with httpx.AsyncClient(timeout=15) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google authorization failed")
        access_token = token_response.json().get("access_token")
        user_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if user_response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve Google profile")

    profile = user_response.json()
    email = (profile.get("email") or "").strip().lower()
    if not profile.get("email_verified") or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A verified Google email is required")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        random_password = secrets.token_urlsafe(32)
        user = User(
            full_name=profile.get("name") or email.split("@")[0],
            email=email,
            hashed_password=get_password_hash(random_password),
            course="General",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_user_token(user)
    redirect = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    _set_access_cookie(redirect, access_token)
    redirect.delete_cookie("google_oauth_state")
    return redirect


@router.post("/forgot-password")
async def forgot_password(request: Request, db: Session = Depends(get_db)):
    data = await _request_data(request)
    email = str(data.get("email") or "").strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if user and settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        reset_token = create_typed_token(
            {"sub": str(user.id), "email": user.email},
            "password_reset",
            timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
        )
        reset_url = f"{settings.APP_BASE_URL.rstrip('/')}/reset-password?token={reset_token}"
        message = EmailMessage()
        message["Subject"] = "Reset your AI Learning Assistant password"
        message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
        message["To"] = user.email
        message.set_content(
            f"Use this link to reset your password:\n\n{reset_url}\n\n"
            f"The link expires in {settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes."
        )
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                smtp.starttls()
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                smtp.send_message(message)
        except smtplib.SMTPException:
            pass

    if not request.headers.get("content-type", "").startswith("application/json"):
        return RedirectResponse(url="/login?password-reset-requested=true", status_code=status.HTTP_303_SEE_OTHER)
    return {"message": "If that email is registered, password reset instructions have been sent."}


@router.post("/reset-password")
async def reset_password(request: Request, db: Session = Depends(get_db)):
    data = await _request_data(request)
    token = str(data.get("token") or "")
    password = str(data.get("password") or "")
    payload = decode_typed_token(token, "password_reset")
    if payload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid or expired")

    is_valid, message = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first() if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset link is invalid")

    user.hashed_password = get_password_hash(password)
    db.add(user)
    db.commit()
    if not request.headers.get("content-type", "").startswith("application/json"):
        return RedirectResponse(url="/login?password-reset=success", status_code=status.HTTP_303_SEE_OTHER)
    return {"message": "Password reset successfully."}

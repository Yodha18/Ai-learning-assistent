from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, get_db, Base, ensure_database_schema
from app.config import settings
from app.utils.helpers import ensure_upload_dir, ensure_vector_store_dir
from app.routers.auth import get_current_active_user, get_optional_current_user
from app.services.progress_service import calculate_overall_progress
from app.services.study_plan_service import get_user_study_plan
import os

# Create database tables and migrate older schema if needed
ensure_database_schema()
Base.metadata.create_all(bind=engine)

# Ensure necessary directories exist
ensure_upload_dir(settings.UPLOAD_DIR)
ensure_vector_store_dir("vector_store")

# Create FastAPI app
app = FastAPI(
    title="AI Learning Assistant",
    description="A personalized AI-powered learning assistant for students",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Import routers
from app.routers import auth, users, subjects, documents, ai_tutor, quizzes, progress, recommendations, study_plan, interview, flashcards, notifications, dashboard

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(subjects.router, prefix="/api/subjects", tags=["Subjects"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(ai_tutor.router, prefix="/api/ai", tags=["AI Tutor"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["Quizzes"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(study_plan.router, prefix="/api/study-plan", tags=["Study Plan"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])
app.include_router(flashcards.router, prefix="/api/flashcards", tags=["Flashcards"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/")
async def root(request: Request):
    """Serve the web landing page to browsers and API metadata to clients."""
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request=request, name="landing.html", context={})
    return {"message": "AI Learning Assistant API", "version": "1.0.0"}


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "google_login_enabled": True,
            "google_login_configured": bool(
                settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
            ),
        },
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={})


@app.get("/forgot-password", include_in_schema=False)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={})


@app.get("/reset-password", include_in_schema=False)
async def reset_password_page(request: Request, token: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={"token": token},
    )


@app.get("/dashboard", include_in_schema=False)
async def dashboard_page(
    request: Request,
    current_user=Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    if current_user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    progress = calculate_overall_progress(db, current_user.id)
    study_plan = get_user_study_plan(db, current_user.id)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": current_user,
            "progress": progress,
            "study_plan": study_plan,
            "subjects_progress": [],
            "weak_topics": [],
            "recommendations": [],
        },
    )


@app.get("/ai-tutor", include_in_schema=False)
async def ai_tutor_page(
    request: Request,
    current_user: any = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """AI Tutor chat page - requires authentication."""
    from app.models.chat import ChatConversation
    
    # Get or create a default conversation for the user
    conversation = db.query(ChatConversation).filter(
        ChatConversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        conversation = ChatConversation(
            user_id=current_user.id,
            title="AI Tutor Chat"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    
    return templates.TemplateResponse(
        request=request,
        name="ai_tutor.html",
        context={"conversation_id": conversation.id}
    )


@app.get("/study-materials", include_in_schema=False)
async def study_materials_page(request: Request):
    return templates.TemplateResponse(request=request, name="study_materials.html", context={})


@app.get("/materials", include_in_schema=False)
async def materials_page(request: Request):
    return templates.TemplateResponse(request=request, name="study_materials.html", context={})


@app.get("/quiz", include_in_schema=False)
async def quiz_page(request: Request):
    return templates.TemplateResponse(request=request, name="quiz.html", context={})


@app.get("/progress", include_in_schema=False)
async def progress_page(
    request: Request,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return templates.TemplateResponse(
        request=request,
        name="progress.html",
        context={"progress": calculate_overall_progress(db, current_user.id)},
    )


@app.get("/study-plan", include_in_schema=False)
async def study_plan_page(
    request: Request,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    study_plan = get_user_study_plan(db, current_user.id)
    return templates.TemplateResponse(
        request=request,
        name="study_plan.html",
        context={"study_plan": study_plan or {"total_study_time": 0, "tasks": []}},
    )


@app.get("/profile", include_in_schema=False)
async def profile_page(request: Request, current_user=Depends(get_current_active_user)):
    return templates.TemplateResponse(request=request, name="profile.html", context={"user": current_user})


@app.get("/settings", include_in_schema=False)
async def settings_page(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html", context={})


@app.get("/more", include_in_schema=False)
async def more_page():
    return RedirectResponse(url="/settings", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "ai_configured": settings.ai_configured,
        "mode": "gemini" if settings.ai_configured else "offline",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
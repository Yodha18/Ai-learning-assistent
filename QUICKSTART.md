# Quick Start Guide - AI Learning Assistant

## Project Structure Overview

```
ai_learning_assistant/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── config.py                 # Configuration settings
│   ├── database.py               # Database setup and session
│   ├── models/                   # SQLAlchemy ORM models
│   ├── schemas/                  # Pydantic data schemas
│   ├── routers/                  # API route handlers
│   ├── services/                 # Business logic services
│   ├── templates/                # HTML templates
│   ├── static/                   # Static files (CSS, JS, images)
│   └── utils/                    # Utility functions
├── stitch_smartstudy_ai_assistant/  # UI Components & Design
│   ├── academic_intelligence/    # Design specs
│   ├── landing_page/             # Landing page
│   ├── login_page/               # Login page
│   ├── registration_page/        # Registration page
│   └── run.py                    # Module info script
├── tests/                        # Test suite
├── alembic/                      # Database migrations
├── requirements.txt              # Python dependencies
├── pytest.ini                    # Pytest configuration
├── run_dev.py                    # Development server starter
└── setup.py                      # Project setup script
```

## Installation & Setup

### 1. Prerequisites
- Python 3.9 or higher
- pip package manager

### 2. Install Dependencies

```bash
# Option A: Automatic setup (Recommended)
python setup.py

# Option B: Manual setup
pip install -r requirements.txt
mkdir -p uploads vector_store logs
cp .env.example .env
```

### 3. Configuration

Edit `.env` file with your settings:

```env
# Database
DATABASE_URL=sqlite:///./ai_learning.db

# Gemini API
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_CHAT_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

# Security (change in production!)
SECRET_KEY=dev-secret-key
```

## Running the Application

### Development Server

```bash
# Option A: Using the dev script
python run_dev.py

# Option B: Direct uvicorn
python -m uvicorn app.main:app --reload

# Option C: Using main.py
python -m app.main
```

The server will start at: **http://127.0.0.1:8000**

### API Documentation

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Available Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get access token
- `GET /api/auth/me` - Get current user profile

### Dashboard
- `GET /api/dashboard/overview` - Dashboard overview data
- `GET /api/dashboard/stats` - Quick statistics
- `GET /api/dashboard/subjects` - Subject progress
- `GET /api/dashboard/weak-topics` - Topics to improve
- `GET /api/dashboard/recommendations` - Personalized recommendations

### Study Materials
- `POST /api/documents/upload` - Upload study materials
- `GET /api/documents/` - List documents
- `GET /api/documents/{id}` - Get specific document

### Quizzes
- `GET /api/quizzes/` - List available quizzes
- `POST /api/quizzes/{id}/attempt` - Start quiz attempt
- `POST /api/quizzes/submit` - Submit quiz answers

### AI Tutor
- `POST /api/ai/chat` - Chat with AI tutor
- `GET /api/ai/conversations` - Get chat history

## Project Modules

### App Directory Structure

#### `routers/`
API route handlers for different features:
- `auth.py` - Authentication routes
- `dashboard.py` - Dashboard routes
- `ai_tutor.py` - AI assistant routes
- `quizzes.py` - Quiz management routes
- `progress.py` - Progress tracking routes
- And more...

#### `services/`
Business logic implementation:
- `auth_service.py` - Authentication logic
- `progress_service.py` - Progress calculation
- `ai_service.py` - AI interactions
- `rag_service.py` - RAG implementation
- And more...

#### `models/`
SQLAlchemy ORM models:
- `user.py` - User model
- `subject.py` - Subject model
- `topic.py` - Topic model
- `quiz.py` - Quiz model
- And more...

### Sub-package: `stitch_smartstudy_ai_assistant/`

This package contains UI components and design specifications:

#### `academic_intelligence/`
- Design specifications in `DESIGN.md`
- Color scheme and visual guidelines

#### `landing_page/`, `login_page/`, `registration_page/`
- HTML templates for each page
- Component documentation

#### Running module utilities
```bash
python stitch_smartstudy_ai_assistant/run.py
```

## Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py

# Run with coverage
pytest --cov=app tests/
```

### Test Configuration

Tests are configured in `pytest.ini` and use fixtures from `tests/conftest.py`.

## Database

### Initialize Database

```bash
# Database is auto-initialized on app startup
python -m uvicorn app.main:app --reload
```

### Run Migrations (if using Alembic)

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

## Common Commands

```bash
# Start development server
python run_dev.py

# Run project setup
python setup.py

# Run tests
pytest -v

# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Check for security issues
pip install bandit
bandit -r app/
```

## Directory as Runnable Modules

Each major directory is now a proper Python package:

- ✅ `app/` - Main FastAPI application (runnable)
- ✅ `stitch_smartstudy_ai_assistant/` - UI components package
  - ✅ `academic_intelligence/` - Runnable module
  - ✅ `landing_page/` - Runnable module
  - ✅ `login_page/` - Runnable module
  - ✅ `registration_page/` - Runnable module
- ✅ `tests/` - Test suite (runnable with pytest)
- ✅ `alembic/` - Database migrations

## Troubleshooting

### Port 8000 already in use
```bash
# Use a different port
python -m uvicorn app.main:app --reload --port 8001
```

### Module not found errors
```bash
# Ensure you're in the project root directory
cd ai_learning_assistant/

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database connection error
```bash
# Check .env file settings
cat .env

# Reset database (development only!)
rm ai_learning.db
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest -v`
4. Format code: `black app/`
5. Submit pull request

## Support

For issues or questions, refer to:
- README.md
- API documentation at /docs
- Code comments and docstrings

---

**Happy Learning! 🚀**

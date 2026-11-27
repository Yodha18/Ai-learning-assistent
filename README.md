# AI-Based Personalized Learning Assistant

A comprehensive, production-quality web application that provides personalized learning assistance to students using AI, RAG (Retrieval-Augmented Generation), and adaptive learning algorithms.

## 🎯 Features

### Core Features
- **AI-Powered Tutor**: Chat with your study materials using advanced AI
- **Document Processing**: Upload PDF, DOCX, and TXT files for automatic processing
- **RAG System**: Intelligent retrieval with source citations and page references
- **Adaptive Quizzes**: AI-generated quizzes that adapt to your skill level
- **Progress Tracking**: Comprehensive progress monitoring with weak topic detection
- **Personalized Recommendations**: AI-driven study recommendations based on performance
- **Study Plans**: Daily personalized study schedules
- **Interview Preparation**: AI-powered technical interview practice
- **Flashcards**: Spaced repetition flashcard system
- **Notifications**: Smart notifications for study reminders and achievements

### Advanced Features
- **Weak Topic Detection**: Explainable algorithm to identify areas needing improvement
- **Adaptive Difficulty**: Quiz difficulty adjusts based on performance
- **Topic Mastery**: Track mastery scores across subjects and topics
- **Study Streaks**: Motivational streak tracking
- **Source Citations**: AI answers include document references with page numbers
- **Multi-format Support**: PDF, DOCX, and TXT file processing
- **User Analytics**: Detailed learning analytics and insights

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (Web Framework)
- SQLAlchemy (ORM)
- Pydantic (Data Validation)
- Uvicorn (ASGI Server)
- PostgreSQL (Database)

**AI & ML:**
- Google Gemini API (Chat & Embeddings)
- FAISS (Vector Database)
- PyMuPDF (PDF Processing)
- python-docx (DOCX Processing)

**Frontend:**
- Jinja2 Templates (Server-rendered)
- Tailwind CSS (Styling)
- Vanilla JavaScript (Interactivity)
- Material Symbols (Icons)

**DevOps:**
- Docker & Docker Compose
- Alembic (Database Migrations)
- pytest (Testing)
- Black (Code Formatting)
- Ruff (Linting)

### Project Structure

```
ai_learning_assistant/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration settings
│   ├── database.py                # Database connection and session
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── user.py
│   │   ├── subject.py
│   │   ├── topic.py
│   │   ├── document.py
│   │   ├── quiz.py
│   │   ├── chat.py
│   │   ├── flashcard.py
│   │   ├── notification.py
│   │   ├── recommendation.py
│   │   ├── study_plan.py
│   │   └── study_session.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── document.py
│   │   ├── quiz.py
│   │   ├── progress.py
│   │   ├── recommendation.py
│   │   ├── study_plan.py
│   │   └── chat.py
│   │
│   ├── routers/                   # API endpoints
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── subjects.py
│   │   ├── documents.py
│   │   ├── ai_tutor.py
│   │   ├── quizzes.py
│   │   ├── progress.py
│   │   ├── recommendations.py
│   │   ├── study_plan.py
│   │   ├── interview.py
│   │   ├── flashcards.py
│   │   ├── notifications.py
│   │   └── dashboard.py
│   │
│   ├── services/                  # Business logic
│   │   ├── auth_service.py
│   │   ├── document_service.py
│   │   ├── rag_service.py
│   │   ├── ai_service.py
│   │   ├── quiz_service.py
│   │   ├── progress_service.py
│   │   ├── recommendation_service.py
│   │   ├── study_plan_service.py
│   │   ├── interview_service.py
│   │   └── notification_service.py
│   │
│   ├── utils/                     # Utility functions
│   │   ├── security.py
│   │   ├── chunking.py
│   │   └── helpers.py
│   │
│   ├── templates/                 # Jinja2 templates
│   │   ├── base.html
│   │   ├── landing.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── ai_tutor.html
│   │   ├── study_materials.html
│   │   ├── quiz.html
│   │   ├── progress.html
│   │   ├── study_plan.html
│   │   ├── profile.html
│   │   └── settings.html
│   │
│   └── static/                    # Static files
│       ├── css/
│       │   └── main.css
│       ├── js/
│       │   └── main.js
│       └── images/
│
├── uploads/                       # User uploaded files
├── vector_store/                  # FAISS vector indices
├── tests/                        # Test files
├── alembic/                      # Database migrations
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── init_db.py
└── README.md
```

## 🚀 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Google Gemini API Key

### Local Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai_learning_assistant
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Set up PostgreSQL database**
```bash
# Create database
createdb ai_learning

# Or using psql
psql -U postgres
CREATE DATABASE ai_learning;
```

6. **Initialize database**
```bash
python init_db.py
```

7. **Run the application**
```bash
uvicorn app.main:app --reload
```

The application will be available at `http://localhost:8000`

### Windows Quick Start

From PowerShell in the project folder:

```powershell
py -3.13 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/`. The application runs with SQLite by default and
includes an offline tutor and quiz fallback when `GEMINI_API_KEY` is empty.
Add a Gemini API key to `.env` to enable generated answers, embeddings, quizzes,
and interview responses.

### Docker Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai_learning_assistant
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your Gemini API key
```

3. **Run with Docker Compose**
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_learning
SECRET_KEY=your_secure_secret_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_CHAT_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=20
```

### Important Security Notes
- Never commit `.env` file to version control
- Use strong, randomly generated `SECRET_KEY`
- Keep your Gemini API key secure
- Change default passwords in production

## 📡 API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key API Endpoints

**Authentication:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

**Subjects & Topics:**
- `GET /api/subjects` - List subjects
- `POST /api/subjects` - Create subject
- `GET /api/subjects/{id}/topics` - List topics
- `POST /api/subjects/{id}/topics` - Create topic

**Documents:**
- `POST /api/documents/upload` - Upload document
- `GET /api/documents` - List documents
- `GET /api/documents/{id}` - Get document details
- `DELETE /api/documents/{id}` - Delete document

**AI Tutor:**
- `POST /api/ai/chat` - Chat with AI
- `GET /api/ai/conversations` - List conversations
- `GET /api/ai/conversations/{id}` - Get conversation details

**Quizzes:**
- `POST /api/quizzes/generate` - Generate AI quiz
- `POST /api/quizzes/{id}/submit` - Submit quiz attempt
- `GET /api/quizzes` - List quizzes
- `GET /api/quizzes/attempts/` - List attempts

**Progress:**
- `GET /api/progress/overall` - Overall progress
- `GET /api/progress/subjects` - Subject progress
- `GET /api/progress/weak-topics` - Weak topics

**Recommendations:**
- `GET /api/recommendations` - Get recommendations
- `POST /api/recommendations/generate` - Generate new recommendations

**Study Plan:**
- `GET /api/study-plan/today` - Today's study plan
- `POST /api/study-plan/generate` - Generate study plan

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/
```

Run tests with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## 📊 RAG Workflow

1. **Document Upload**: User uploads PDF/DOCX/TXT file
2. **Text Extraction**: Extract text while preserving page numbers
3. **Text Cleaning**: Clean and normalize extracted text
4. **Text Chunking**: Split text into meaningful chunks (500-1000 tokens)
5. **Embedding Generation**: Create Gemini embeddings for each chunk
6. **Vector Storage**: Store embeddings in FAISS with metadata
7. **Query Processing**: When user asks a question:
   - Generate query embedding
   - Search user's vector store
   - Retrieve relevant chunks
   - Send context to Gemini
   - Generate answer with citations

## 🔐 Security

- **Password Hashing**: Uses bcrypt for secure password storage
- **JWT Authentication**: Token-based authentication with expiration
- **Input Validation**: Pydantic schemas for all inputs
- **File Validation**: File type and size restrictions
- **Ownership Checks**: Users can only access their own data
- **Environment Variables**: Sensitive data never in source code

## 🎨 Design

The application uses a modern, clean design based on Material Design principles:
- **Color Palette**: Primary (indigo), Secondary (green), Error (red)
- **Typography**: Inter (body), Outfit (headings)
- **Components**: Material Symbols icons, rounded corners, subtle shadows
- **Responsive**: Mobile-first design with breakpoints

## 📈 Key Algorithms

### Weak Topic Detection
A topic is considered weak when:
- At least 3 quiz attempts exist
- Accuracy is below 60%
- Priority: High (<50%), Medium (50-60%)

### Adaptive Quiz Difficulty
- Accuracy < 50%: Easy questions
- Accuracy 50-75%: Medium questions  
- Accuracy > 75%: Hard questions

### Spaced Repetition (Flashcards)
Based on SM-2 algorithm:
- **Again**: Reset interval, decrease ease factor
- **Hard**: Slight interval increase, decrease ease factor
- **Good**: Normal interval increase
- **Easy**: Larger interval increase, increase ease factor

## 🚀 Deployment

### Production Considerations
- Use environment-specific configuration
- Enable HTTPS
- Use production database (managed PostgreSQL)
- Implement rate limiting
- Add monitoring and logging
- Use secret management for API keys
- Enable CORS for specific domains only
- Implement backup strategy for database and uploads

### Docker Production
```bash
docker-compose -f docker-compose.yml up -d
```

## 📝 Development

### Code Quality
```bash
# Format code
black app/

# Lint code
ruff check app/

# Type checking
mypy app/
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🤝 Contributing

This is a demonstration project. For contributions:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please ensure you have proper licenses for any third-party APIs or services used.

## 🙏 Acknowledgments

- Gemini for chat and embedding APIs
- FAISS for vector similarity search
- FastAPI for the web framework
- Material Design for design inspiration
- The open-source Python community

## 📞 Support

For issues, questions, or suggestions, please open an issue in the repository.

---

**Built with ❤️ for students and learners**
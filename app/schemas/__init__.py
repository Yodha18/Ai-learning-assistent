from app.schemas.auth import UserCreate, UserLogin, TokenResponse
from app.schemas.user import UserUpdate, UserResponse
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentChunkResponse
from app.schemas.quiz import QuizCreate, QuizGenerateRequest, QuizResponse, QuizWithQuestions, QuizAttemptCreate, QuizAttemptResponse, QuizAttemptWithDetails
from app.schemas.progress import SubjectProgress, TopicProgress, OverallProgress, WeakTopic
from app.schemas.recommendation import RecommendationCreate, RecommendationResponse
from app.schemas.chat import ChatMessageCreate, ChatConversationCreate, ChatConversationResponse, ChatMessageResponse, ChatConversationWithMessages, ChatRequest, ChatResponse
from app.schemas.study_plan import StudyTaskCreate, StudyTaskResponse, StudyPlanCreate, StudyPlanResponse, StudyPlanWithTasks, StudyPlanGenerateRequest

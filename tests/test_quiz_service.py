from app.models.document import Document, DocumentChunk, ProcessingStatus
from app.models.subject import Subject
from app.models.user import User
from app.schemas.quiz import QuizGenerateRequest
from app.services.quiz_service import generate_ai_quiz


def test_quiz_generation_uses_selected_subject_notes(db, monkeypatch):
    user = User(
        full_name="Quiz Test User",
        email="quiz-context@example.com",
        hashed_password="not-used-in-this-test",
        course="Science",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    subject = Subject(name="Physics", user_id=user.id)
    db.add(subject)
    db.commit()
    db.refresh(subject)

    document = Document(
        original_filename="physics.txt",
        file_path="unused-in-test.txt",
        file_type=".txt",
        file_size=64,
        user_id=user.id,
        subject_id=subject.id,
        processing_status=ProcessingStatus.READY,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    db.add(DocumentChunk(
        document_id=document.id,
        chunk_text="Newton's laws relate force and momentum.",
        chunk_index=0,
    ))
    db.commit()

    captured = {}

    def generate_questions(**kwargs):
        captured.update(kwargs)
        return [{
            "question_text": "What do Newton's laws relate?",
            "options": ["Force and momentum", "Grammar and syntax", "Cells and genes", "Supply and demand"],
            "correct_answer": 0,
            "explanation": "The notes explain the relationship.",
            "topic": kwargs["topic"],
        }]

    monkeypatch.setattr("app.services.quiz_service.ai_service.generate_quiz", generate_questions)

    quiz = generate_ai_quiz(
        db,
        QuizGenerateRequest(subject_id=subject.id, difficulty="medium", number_of_questions=1),
        user.id,
    )

    assert captured["topic"] == "Physics"
    assert "Newton's laws" in captured["context"]
    assert quiz.subject_id == subject.id
    assert len(quiz.questions) == 1
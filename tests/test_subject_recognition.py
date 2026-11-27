from app.services.subject_recognition import detect_subject
from app.models.document import Document, ProcessingStatus
from app.models.subject import Subject
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services import document_service


def test_detects_subject_from_distinctive_document_terms():
    text = "Newton's laws describe force and momentum. Kinematics relates velocity to time."

    assert detect_subject(text) == "Physics"


def test_explicit_subject_in_filename_is_enough_to_classify():
    assert detect_subject("Course notes and lecture material", "Organic Chemistry.pdf") == "Chemistry"


def test_ambiguous_text_does_not_create_a_subject_guess():
    assert detect_subject("These are notes for next week's lecture.") is None


def test_processing_upload_creates_and_reuses_detected_subject(db, tmp_path, monkeypatch):
    monkeypatch.setattr(document_service.settings, "GEMINI_API_KEY", "")
    user = User(
        full_name="Subject Test User",
        email="subject-detection@example.com",
        hashed_password="not-used-in-this-test",
        course="Science",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    documents = []
    for filename in ("physics-lecture.txt", "physics-review.txt"):
        path = tmp_path / filename
        path.write_text(
            "Newton's laws describe force and momentum. Kinematics relates velocity to time.",
            encoding="utf-8",
        )
        document = Document(
            original_filename=filename,
            file_path=str(path),
            file_type=".txt",
            file_size=path.stat().st_size,
            user_id=user.id,
            processing_status=ProcessingStatus.UPLOADING,
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        documents.append(document_service.process_document(db, document))

    subjects = db.query(Subject).filter(Subject.user_id == user.id).all()
    assert len(subjects) == 1
    assert subjects[0].name == "Physics"
    assert all(document.subject_id == subjects[0].id for document in documents)
    assert all(document.chunks[0].subject == "Physics" for document in documents)
    assert DocumentResponse.model_validate(documents[0]).subject_name == "Physics"
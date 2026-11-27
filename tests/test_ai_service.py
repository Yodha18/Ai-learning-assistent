from app.services.ai_service import AIService


def test_build_learning_memory_creates_student_summary():
    ai_service = AIService()
    history = [
        {"role": "user", "content": "Explain the difference between a primary key and a foreign key."},
        {"role": "assistant", "content": "A primary key uniquely identifies records..."},
        {"role": "user", "content": "Can you give a simple real-world example?"},
        {"role": "assistant", "content": "Sure, imagine a student table..."},
    ]

    memory = ai_service._build_learning_memory(history)

    assert "primary key" in memory.lower()
    assert "real-world" in memory.lower() or "example" in memory.lower()
    assert len(memory) > 40


def test_generate_quiz_falls_back_to_uploaded_notes_when_ai_fails(monkeypatch):
    ai_service = AIService()

    def fail_ai_request():
        raise RuntimeError("insufficient_quota")

    monkeypatch.setattr(ai_service, "_get_client", fail_ai_request)
    monkeypatch.setattr("app.services.ai_service.settings.GEMINI_API_KEY", "configured")

    questions = ai_service.generate_quiz(
        topic="Physics",
        num_questions=3,
        context="Newton's laws relate force and momentum. Kinematics describes motion.",
    )

    assert len(questions) == 3
    assert "Newton's laws" in questions[0]["options"][questions[0]["correct_answer"]]
    assert questions[0]["topic"] == "Physics"


def test_generate_chat_response_falls_back_when_ai_request_fails(monkeypatch):
    ai_service = AIService()

    def fail_ai_request():
        raise RuntimeError("quota exceeded")

    monkeypatch.setattr(ai_service, "_get_client", fail_ai_request)
    monkeypatch.setattr("app.services.ai_service.settings.GEMINI_API_KEY", "configured")

    response = ai_service.generate_chat_response(
        "What is Newton's first law?",
        [
            {
                "chunk_text": "Newton's first law states that an object remains at rest or in uniform motion unless acted on by a force.",
                "source_name": "Physics Notes",
                "page_number": 2,
            }
        ],
    )

    assert "Newton's first law" in response["answer"]


def test_general_chat_does_not_inject_unrelated_document_history(monkeypatch):
    ai_service = AIService()
    captured = {}

    class FakeGeminiClient:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return "Photosynthesis is how plants convert light into chemical energy."

    monkeypatch.setattr(ai_service, "_get_client", lambda: FakeGeminiClient())
    monkeypatch.setattr("app.services.ai_service.settings.GEMINI_API_KEY", "configured")

    ai_service.generate_chat_response(
        "What is photosynthesis?",
        [],
        conversation_history=[
            {"role": "user", "content": "Summarize my XAI research paper."},
            {"role": "assistant", "content": "Your paper discusses explainable AI."},
        ],
    )

    messages = captured["messages"]
    assert len(messages) == 2
    assert messages[-1]["content"] == "What is photosynthesis?"
    assert "XAI" not in messages[0]["content"]
    assert captured["max_output_tokens"] == 450

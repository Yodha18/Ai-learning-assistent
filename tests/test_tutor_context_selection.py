import asyncio

from app.routers.ai_tutor import AsyncTutorCoordinator, GreetingResponder, TutorProfile
from app.services import ai_service as ai_service_module


class StaticProfileRouter:
    def select(self, question, explanation_style):
        return TutorProfile(name="default")


def test_general_question_skips_documents_and_web(monkeypatch):
    coordinator = AsyncTutorCoordinator(StaticProfileRouter())
    generated = {}

    def unexpected_retrieval(*args, **kwargs):
        raise AssertionError("general questions should not retrieve documents")

    def fake_generate(question, context_chunks, *args, **kwargs):
        generated["chunks"] = context_chunks
        return {"answer": "Direct answer.", "sources": []}

    monkeypatch.setattr(coordinator, "_search_context", unexpected_retrieval)
    monkeypatch.setattr(ai_service_module.ai_service, "generate_chat_response", fake_generate)

    response = asyncio.run(
        coordinator.generate_response(
            user_id=1,
            question="Why is the sky blue?",
            explanation_style="simple",
            conversation_history=[],
        )
    )

    assert response["answer"] == "Direct answer."
    assert generated["chunks"] == []


def test_selected_document_is_retrieved_for_question(monkeypatch):
    coordinator = AsyncTutorCoordinator(StaticProfileRouter())
    retrieved = {}

    def fake_retrieval(user_id, question, document_id=None):
        retrieved["document_id"] = document_id
        return [{"chunk_text": "Paper content", "document_id": document_id}]

    def fake_generate(question, context_chunks, *args, **kwargs):
        return {"answer": context_chunks[0]["chunk_text"], "sources": []}

    monkeypatch.setattr(coordinator, "_search_context", fake_retrieval)
    monkeypatch.setattr(ai_service_module.ai_service, "generate_chat_response", fake_generate)

    response = asyncio.run(
        coordinator.generate_response(
            user_id=1,
            question="Summarize this section.",
            explanation_style="simple",
            conversation_history=[],
            document_id=42,
        )
    )

    assert retrieved["document_id"] == 42
    assert response["answer"] == "Paper content"


def test_web_search_requires_explicit_request():
    assert not AsyncTutorCoordinator._wants_web_research("What is photosynthesis?")
    assert AsyncTutorCoordinator._wants_web_research("Search online for recent astronomy sources.")


def test_small_talk_greeting_gets_a_short_reply():
    response = GreetingResponder().respond("How are you, brother?")

    assert response == {
        "answer": "I'm doing well, thanks for asking! How can I help?",
        "sources": [],
    }

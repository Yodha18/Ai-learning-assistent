from types import SimpleNamespace

from app.services.gemini_service import GeminiClient


def test_generate_content_sends_gemini_roles_and_system_instruction(monkeypatch):
    client = GeminiClient.__new__(GeminiClient)
    client._headers = {"x-goog-api-key": "test-key"}
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return SimpleNamespace(
            is_error=False,
            json=lambda: {
                "candidates": [
                    {"content": {"parts": [{"text": "A concise answer."}]}}
                ]
            },
        )

    monkeypatch.setattr("app.services.gemini_service.httpx.post", fake_post)
    answer = client.generate_content(
        [
            {"role": "system", "content": "Be clear."},
            {"role": "user", "content": "Explain gravity."},
            {"role": "assistant", "content": "It is a force."},
            {"role": "user", "content": "Give an example."},
        ],
        model="gemini-test",
    )

    assert answer == "A concise answer."
    assert captured["url"].endswith("/models/gemini-test:generateContent")
    assert captured["json"]["systemInstruction"]["parts"][0]["text"] == "Be clear."
    assert [item["role"] for item in captured["json"]["contents"]] == [
        "user",
        "model",
        "user",
    ]


def test_embed_contents_parses_vectors(monkeypatch):
    client = GeminiClient.__new__(GeminiClient)
    client._headers = {"x-goog-api-key": "test-key"}
    captured = {}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            is_error=False,
            json=lambda: {"embeddings": [{"values": [0.1, 0.2]}]},
        )

    monkeypatch.setattr("app.services.gemini_service.httpx.post", fake_post)
    vectors = client.embed_contents(["study material"], task_type="RETRIEVAL_DOCUMENT")

    assert vectors == [[0.1, 0.2]]
    request = captured["json"]["requests"][0]
    assert request["taskType"] == "RETRIEVAL_DOCUMENT"
    assert request["outputDimensionality"] == 768

from app.config import Settings


def test_settings_ignore_legacy_openai_variables(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_CHAT_MODEL=gpt-4o-mini\n"
        "OPENAI_EMBEDDING_MODEL=text-embedding-ada-002\n"
        "GEMINI_API_KEY=test-gemini-key\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.GEMINI_API_KEY == "test-gemini-key"
    assert settings.ai_configured is True

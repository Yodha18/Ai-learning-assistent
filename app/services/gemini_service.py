"""Small synchronous client for the Google Gemini REST API."""

from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings


class GeminiClient:
    _base_url = "https://generativelanguage.googleapis.com/v1beta"
    embedding_dimensions = 768

    def __init__(self) -> None:
        if not settings.gemini_configured:
            raise ValueError("GEMINI_API_KEY is not configured. Add it to your .env file.")
        self._headers = {"x-goog-api-key": settings.GEMINI_API_KEY}

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self._base_url}/{endpoint}",
            headers=self._headers,
            json=payload,
            timeout=60,
        )
        if response.is_error:
            raise RuntimeError(
                f"Gemini API request failed ({response.status_code}): "
                f"{response.text[:500]}"
            )
        return response.json()

    def generate_content(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.6,
        max_output_tokens: int = 900,
        response_mime_type: str | None = None,
    ) -> str:
        system_instructions = []
        contents = []
        for message in messages:
            text = message.get("content", "")
            if not text:
                continue
            if message.get("role") == "system":
                system_instructions.append(text)
            else:
                role = "model" if message.get("role") == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": text}]})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }
        if system_instructions:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_instructions)}]
            }
        if response_mime_type:
            payload["generationConfig"]["responseMimeType"] = response_mime_type

        model_name = quote(model or settings.GEMINI_CHAT_MODEL, safe="-_.")
        result = self._post(f"models/{model_name}:generateContent", payload)
        candidates = result.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no generated content.")
        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part["text"] for part in parts if isinstance(part.get("text"), str)]
        if not text_parts:
            raise RuntimeError("Gemini returned an empty response.")
        return "\n".join(text_parts)

    def embed_contents(self, texts: list[str], *, task_type: str) -> list[list[float]]:
        if not texts:
            return []
        model_name = quote(settings.GEMINI_EMBEDDING_MODEL, safe="-_.")
        result = self._post(
            f"models/{model_name}:batchEmbedContents",
            {
                "requests": [
                    {
                        "model": f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                        "content": {"parts": [{"text": text}]},
                        "taskType": task_type,
                        "outputDimensionality": self.embedding_dimensions,
                    }
                    for text in texts
                ]
            },
        )
        embeddings = result.get("embeddings") or []
        if len(embeddings) != len(texts):
            raise RuntimeError("Gemini returned an unexpected number of embeddings.")
        return [item["values"] for item in embeddings]

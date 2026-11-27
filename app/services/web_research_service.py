import json
import logging
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen

from app.config import settings

logger = logging.getLogger(__name__)


class WebResearchService:
    """Retrieve concise, citable web context through SerpApi."""

    _endpoint = "https://serpapi.com/search.json"

    def search(self, question: str, limit: int = 3) -> list[dict[str, Any]]:
        if not settings.SERPAPI_API_KEY:
            return []

        query = urlencode(
            {
                "engine": "google",
                "q": question,
                "api_key": settings.SERPAPI_API_KEY,
                "num": limit,
            }
        )
        try:
            with urlopen(f"{self._endpoint}?{query}", timeout=10) as response:
                payload = json.load(response)
        except (OSError, ValueError) as error:
            logger.warning("Web research request failed: %s", error)
            return []

        results: list[dict[str, Any]] = []
        for item in payload.get("organic_results", [])[:limit]:
            title = item.get("title")
            link = item.get("link")
            snippet = item.get("snippet")
            if not all(isinstance(value, str) and value.strip() for value in (title, link, snippet)):
                continue
            results.append(
                {
                    "chunk_text": f"{title}\n{snippet}",
                    "document_id": None,
                    "page_number": None,
                    "subject": "Web research",
                    "topic": question,
                    "source_name": title,
                    "url": link,
                }
            )
        return results


web_research_service = WebResearchService()

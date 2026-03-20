"""WHO Disease Outbreak News adapter.

Source: https://www.who.int/api/news/diseaseoutbreaknews
Auth: None required
TTL: 24 hours

Signal: Active disease outbreaks → supply chain disruption, labor market impact,
commodity demand shifts, travel/trade route closure risk.
"""

import re
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


WHO_API_URL = "https://www.who.int/api/news/diseaseoutbreaknews"

# Attempt to extract disease name from common title patterns
# e.g. "Mpox in Democratic Republic of Congo" → "Mpox"
# e.g. "Yellow Fever – Brazil" → "Yellow Fever"
DISEASE_PATTERN = re.compile(
    r"^([A-Za-z\s\-/()]+?)(?:\s+[-–—in]+\s+[A-Z]|\s*[-–—]\s*[A-Z])",
    re.IGNORECASE,
)

# Strip HTML tags
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    clean = HTML_TAG_PATTERN.sub(" ", text)
    return re.sub(r"\s+", " ", clean).strip()


def _extract_disease(title: str) -> str | None:
    """Best-effort disease name extraction from outbreak title."""
    match = DISEASE_PATTERN.match(title)
    if match:
        candidate = match.group(1).strip().rstrip("-–—").strip()
        if len(candidate) > 2:
            return candidate
    return None


def _extract_countries(title: str) -> list[str]:
    """Best-effort country extraction from outbreak title.

    Looks for patterns like:
    - "Avian influenza – situation in Egypt" → ["Egypt"]
    - "Mpox in Democratic Republic of Congo" → ["Democratic Republic of Congo"]
    - "Yellow Fever – Brazil" → ["Brazil"]
    - "Cholera - Multiple Countries" → []
    """
    # Pattern: "situation in COUNTRY" or "cases in COUNTRY"
    situation_match = re.search(
        r"(?:situation|cases|outbreak|update)\s+in\s+([A-Z][^,\-–—]+?)(?:\s*$|\s*,|\s*[-–—])",
        title,
        re.IGNORECASE,
    )
    if situation_match:
        country = situation_match.group(1).strip()
        if country.lower() not in ("multiple countries", "several countries"):
            return [country]

    # Pattern: title ends with "– COUNTRY" or "- COUNTRY" (no "situation in")
    dash_match = re.search(
        r"[-–—]\s*(?:situation\s+in\s+)?([A-Z][A-Za-z\s]+?)(?:\s*$|\s*,)",
        title,
    )
    if dash_match:
        country = dash_match.group(1).strip()
        skip = ("multiple countries", "several countries", "update", "global situation update",
                "global update", "global situation")
        if country.lower() not in skip and not country.lower().startswith("global"):
            return [country]

    # Pattern: "in COUNTRY" anywhere
    in_match = re.search(r"\bin\s+([A-Z][A-Za-z\s]{3,40}?)(?:\s*$|\s*,|\s+and\b)", title)
    if in_match:
        country = in_match.group(1).strip()
        if country.lower() not in ("multiple countries", "several countries"):
            return [country]

    return []


class WhoOutbreaksAdapter(GhostMarketAdapter):
    """WHO Disease Outbreak News adapter with cache-first pattern.

    Fetches active outbreak notices from WHO DON API.
    Returns structured outbreak data for signal interpretation by agent layer.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 24 hours (WHO updates once daily)."""
        return 86400

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "who_outbreaks"

    async def fetch(self, query: dict) -> dict:  # noqa: ARG002
        """Cache-first fetch of WHO Disease Outbreak News.

        Args:
            query: Unused (no per-query params; fetches full outbreak list)

        Returns:
            {
                "source": "who_outbreaks",
                "fetched_at": str (ISO timestamp),
                "active_notices": [
                    {
                        "title": str,
                        "disease": str | None,
                        "countries": [str],
                        "published_at": str,
                        "summary": str,
                        "url": str,
                    },
                    ...
                ],
                "notice_count": int
            }
        """
        cache_key = "who_outbreaks_full"

        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        data = await self._call_who_api()

        await self._cache_store(cache_key, data)
        return data

    async def _call_who_api(self) -> dict:
        """Call WHO DON API and normalize response."""
        headers = {
            "User-Agent": "SignalDispatch/1.0",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(WHO_API_URL, headers=headers, timeout=30.0)
                response.raise_for_status()
                raw = response.json()

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 429:
                raise GhostMarketApiError(
                    "WHO API rate limit exceeded", status_code=429, retryable=True
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"WHO API server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"WHO API HTTP error: {status_code}", status_code=status_code
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to WHO API", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "WHO API request timed out", retryable=True
            ) from e

        # WHO API may return a list directly or {"value": [...]}
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            items = raw.get("value", raw.get("items", raw.get("data", [])))
        else:
            items = []

        notices = []
        for item in items:
            title = item.get("Title") or item.get("title") or ""
            summary_raw = item.get("Summary") or item.get("summary") or ""
            summary = _strip_html(summary_raw)[:500]
            published_raw = item.get("PublicationDate") or item.get("publicationDate") or ""
            url = item.get("Url") or item.get("url") or item.get("link") or ""

            # Normalize published_at to ISO
            published_at = published_raw
            if published_raw and not published_raw.endswith("Z") and "T" not in str(published_raw):
                try:
                    dt = datetime.strptime(str(published_raw)[:10], "%Y-%m-%d")
                    published_at = dt.replace(tzinfo=timezone.utc).isoformat()
                except ValueError:
                    published_at = str(published_raw)

            notices.append({
                "title": title,
                "disease": _extract_disease(title),
                "countries": _extract_countries(title),
                "published_at": published_at,
                "summary": summary,
                "url": url,
            })

        return {
            "source": "who_outbreaks",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "active_notices": notices,
            "notice_count": len(notices),
        }

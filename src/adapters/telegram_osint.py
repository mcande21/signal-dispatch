"""Telegram OSINT adapter for Signal Dispatch.

Scrapes public Telegram channel web previews at https://t.me/s/{channel}.
No authentication required. Covers conflict/OSINT channels across Ukraine/Russia,
Middle East, and geopolitics beats.

Usage:
    adapter = TelegramOsintAdapter()
    result = await adapter.fetch()
    # or with custom options:
    result = await adapter.fetch(max_messages=20, hours_back=24)
"""

import asyncio
import re
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Channel registry
# ---------------------------------------------------------------------------

CHANNELS: dict[str, dict[str, str]] = {
    # Ukraine / Russia conflict
    "CIG_telegram": {
        "name": "Conflict Intelligence Team",
        "category": "ukraine_russia",
    },
    "DeepStateUA": {
        "name": "DeepState Ukraine",
        "category": "ukraine_russia",
    },
    "wartranslated": {
        "name": "War Translated",
        "category": "ukraine_russia",
    },
    "GeneralStaffZSU": {
        "name": "Ukrainian General Staff",
        "category": "ukraine_russia",
    },
    "mod_russia": {
        "name": "Russian MoD",
        "category": "ukraine_russia",
    },
    "operativnoZSU": {
        "name": "ZSU Operative",
        "category": "ukraine_russia",
    },
    "intelslava": {
        "name": "Intel Slava Z",
        "category": "ukraine_russia",
    },
    "RVvoenkor": {
        "name": "Voenkor RV",
        "category": "ukraine_russia",
    },
    "readovkanews": {
        "name": "Readovka",
        "category": "ukraine_russia",
    },
    "legitimniy": {
        "name": "Legitimniy",
        "category": "ukraine_russia",
    },
    "ukraine_frontline": {
        "name": "Ukraine Frontline",
        "category": "ukraine_russia",
    },
    # Middle East
    "middleeastosint": {
        "name": "Middle East OSINT",
        "category": "middle_east",
    },
    "inikiforv": {
        "name": "Nikiforov OSINT",
        "category": "middle_east",
    },
    # Geopolitics
    "geaborning": {
        "name": "Geo A. Borning",
        "category": "geopolitics",
    },
    "TheIntelligencer": {
        "name": "The Intelligencer",
        "category": "geopolitics",
    },
    # Finance channels -- skipped by default (low signal for Signal Dispatch)
    # "WallStreetSilver": {"name": "Wall St Silver", "category": "finance"},
    # "unusual_whales": {"name": "Unusual Whales", "category": "finance"},
}

# ---------------------------------------------------------------------------
# Urgency keyword patterns (case-insensitive)
# ---------------------------------------------------------------------------

URGENCY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("BREAKING", re.compile(r"\bbreaking\b", re.IGNORECASE)),
    ("ALERT", re.compile(r"\balert\b", re.IGNORECASE)),
    ("URGENT", re.compile(r"\burgent\b", re.IGNORECASE)),
    ("FLASH", re.compile(r"\bflash\b", re.IGNORECASE)),
    ("explosion", re.compile(r"\bexplosion[s]?\b", re.IGNORECASE)),
    ("strike", re.compile(r"\bstrike[s]?\b", re.IGNORECASE)),
    ("missile", re.compile(r"\bmissile[s]?\b", re.IGNORECASE)),
    ("drone attack", re.compile(r"\bdrone\s+attack[s]?\b", re.IGNORECASE)),
    ("nuclear", re.compile(r"\bnuclear\b", re.IGNORECASE)),
    ("radiation", re.compile(r"\bradiation\b", re.IGNORECASE)),
    ("escalation", re.compile(r"\bescalation\b", re.IGNORECASE)),
    ("ceasefire", re.compile(r"\bceasefire\b", re.IGNORECASE)),
    ("surrender", re.compile(r"\bsurrender\b", re.IGNORECASE)),
    ("withdrawal", re.compile(r"\bwithdrawal\b", re.IGNORECASE)),
    ("sanctions", re.compile(r"\bsanctions\b", re.IGNORECASE)),
    ("designated", re.compile(r"\bdesignated\b", re.IGNORECASE)),
    ("blacklisted", re.compile(r"\bblacklisted?\b", re.IGNORECASE)),
]

# Delay between channel requests (seconds) -- polite scraping
REQUEST_DELAY = 1.5

# Browser-like headers to avoid bot detection
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ---------------------------------------------------------------------------
# Message parsing
# ---------------------------------------------------------------------------


def _extract_messages(html: str, max_messages: int, hours_back: int) -> list[dict]:
    """Parse Telegram channel web preview HTML into message dicts.

    Args:
        html: Raw HTML from https://t.me/s/{channel}
        max_messages: Maximum number of messages to return
        hours_back: Only include messages within this many hours

    Returns:
        List of dicts with keys: text, time (ISO str)
        Sorted newest-first. Empty list if parsing fails or no messages found.
    """
    soup = BeautifulSoup(html, "html.parser")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    messages: list[dict] = []

    # Each message lives inside a .tgme_widget_message_wrap container.
    # The actual text is in .tgme_widget_message_text (may be absent for
    # media-only posts). The timestamp is in a <time datetime="..."> element.
    wraps = soup.select("div.tgme_widget_message_wrap")

    for wrap in wraps:
        # Extract timestamp
        time_el = wrap.select_one("time[datetime]")
        if not time_el:
            continue

        datetime_attr = time_el.get("datetime", "")
        if not datetime_attr:
            continue

        try:
            msg_time = datetime.fromisoformat(str(datetime_attr).replace("Z", "+00:00"))
        except ValueError:
            continue

        # Apply time filter
        if msg_time < cutoff:
            continue

        # Extract text -- may be absent (media-only post)
        text_el = wrap.select_one(".tgme_widget_message_text")
        if not text_el:
            # Try the broader message bubble text area
            text_el = wrap.select_one(".tgme_widget_message_bubble")

        if text_el:
            # Get text content, collapse whitespace
            raw_text = text_el.get_text(separator=" ", strip=True)
            # Collapse multiple spaces/newlines
            raw_text = re.sub(r"\s+", " ", raw_text).strip()
        else:
            raw_text = ""

        if not raw_text:
            continue

        messages.append({
            "text": raw_text,
            "time": msg_time.isoformat(),
        })

    # Sort newest-first
    messages.sort(key=lambda m: m["time"], reverse=True)

    return messages[:max_messages]


def _detect_urgency(text: str) -> list[str]:
    """Return list of urgency keyword labels found in text.

    Args:
        text: Message text

    Returns:
        Sorted list of matched keyword labels (e.g. ["BREAKING", "strike"])
    """
    matched = []
    for label, pattern in URGENCY_PATTERNS:
        if pattern.search(text):
            matched.append(label)
    return sorted(matched)


def _cross_validate(
    channels_data: dict[str, dict],
) -> list[dict]:
    """Identify events reported by 2+ channels (highest-signal output).

    Uses urgency keyword overlap as a lightweight event-fingerprint:
    channels that both mention the same keyword set within a 6-hour window
    are considered co-reporting the same event.

    Args:
        channels_data: Populated channel dicts (same structure as return shape)

    Returns:
        List of cross-validation dicts: {event, channels, confidence}
    """
    # Build index: keyword -> [(channel_id, message_time), ...]
    keyword_index: dict[str, list[tuple[str, str]]] = {}

    for channel_id, channel_info in channels_data.items():
        for msg in channel_info.get("urgent", []):
            msg_time = msg.get("time", "")
            for kw in msg.get("keywords", []):
                keyword_index.setdefault(kw, []).append((channel_id, msg_time))

    cross_validated: list[dict] = []
    seen_keyword_sets: set[frozenset[str]] = set()

    for keyword, occurrences in keyword_index.items():
        if len(occurrences) < 2:
            continue

        # Group by channels that reported within 6h of each other
        # Sort by time to enable window comparison
        try:
            sorted_occ = sorted(occurrences, key=lambda x: x[1])
        except Exception:
            continue

        # Sliding window: find clusters within 6 hours
        window_hours = 6
        i = 0
        while i < len(sorted_occ):
            anchor_time_str = sorted_occ[i][1]
            try:
                anchor_time = datetime.fromisoformat(anchor_time_str)
            except ValueError:
                i += 1
                continue

            cluster_channels: list[str] = [sorted_occ[i][0]]
            j = i + 1
            while j < len(sorted_occ):
                try:
                    candidate_time = datetime.fromisoformat(sorted_occ[j][1])
                except ValueError:
                    j += 1
                    continue
                delta = abs((candidate_time - anchor_time).total_seconds())
                if delta <= window_hours * 3600:
                    cluster_channels.append(sorted_occ[j][0])
                j += 1

            # De-duplicate channels in cluster
            unique_channels = list(dict.fromkeys(cluster_channels))

            if len(unique_channels) >= 2:
                key = frozenset(unique_channels)
                if key not in seen_keyword_sets:
                    seen_keyword_sets.add(key)
                    cross_validated.append({
                        "event": keyword,
                        "channels": unique_channels,
                        "confidence": "high",
                    })

            i += 1

    return cross_validated


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class TelegramOsintAdapter:
    """Scrapes public Telegram channel previews for conflict/OSINT signals.

    Public web previews only -- no authentication, no Telegram API key needed.
    Suitable for channels that expose their preview at https://t.me/s/{channel}.

    Channels polled (15 active):
    - 11 Ukraine/Russia conflict channels
    - 2 Middle East OSINT channels
    - 2 geopolitics channels
    Finance channels (WallStreetSilver, unusual_whales) are excluded by default.
    """

    BASE_URL = "https://t.me/s"

    def __init__(self, channels: dict[str, dict[str, str]] | None = None) -> None:
        """Initialize adapter.

        Args:
            channels: Override default channel registry. Each key is a channel
                handle; each value must have "name" and "category" keys.
        """
        self._channels = channels if channels is not None else CHANNELS

    async def _fetch_channel_html(
        self,
        client: httpx.AsyncClient,
        channel_id: str,
    ) -> str | None:
        """Fetch raw HTML for a single channel preview page.

        Args:
            client: Shared httpx client
            channel_id: Telegram channel handle (no @)

        Returns:
            HTML string, or None on error (403, timeout, empty, etc.)
        """
        url = f"{self.BASE_URL}/{channel_id}"
        try:
            response = await client.get(url, headers=HEADERS, timeout=15.0, follow_redirects=True)
            if response.status_code == 403:
                return None
            if response.status_code == 404:
                return None
            response.raise_for_status()
            text = response.text
            # Guard against empty or near-empty pages
            if len(text) < 500:
                return None
            return text
        except httpx.TimeoutException:
            return None
        except httpx.HTTPStatusError:
            return None
        except httpx.RequestError:
            return None

    async def fetch(
        self,
        max_messages: int = 20,
        hours_back: int = 24,
    ) -> dict:
        """Scrape all configured channels and return structured signal data.

        Args:
            max_messages: Max messages per channel (capped at 20 per spec)
            hours_back: Only include messages within this many hours (default 24)

        Returns:
            Structured dict matching Signal Dispatch return shape -- see module
            docstring for full schema.
        """
        max_messages = min(max_messages, 20)

        channels_output: dict[str, dict] = {}
        channels_failed = 0
        total_messages = 0
        urgent_messages = 0
        keyword_counts: dict[str, int] = {}

        async with httpx.AsyncClient() as client:
            channel_ids = list(self._channels.keys())
            for idx, channel_id in enumerate(channel_ids):
                channel_meta = self._channels[channel_id]

                html = await self._fetch_channel_html(client, channel_id)

                if html is None:
                    channels_failed += 1
                    # Add delay even on failure to respect rate limits
                    if idx < len(channel_ids) - 1:
                        await asyncio.sleep(REQUEST_DELAY)
                    continue

                messages = _extract_messages(html, max_messages=max_messages, hours_back=hours_back)

                if not messages:
                    # Channel reachable but no recent messages -- still count as polled
                    channels_output[channel_id] = {
                        "name": channel_meta["name"],
                        "category": channel_meta["category"],
                        "messages": 0,
                        "latest_time": "",
                        "urgent": [],
                        "recent": [],
                    }
                    if idx < len(channel_ids) - 1:
                        await asyncio.sleep(REQUEST_DELAY)
                    continue

                # Split urgent vs recent
                urgent: list[dict] = []
                recent_non_urgent: list[dict] = []

                for msg in messages:
                    keywords = _detect_urgency(msg["text"])
                    truncated = msg["text"][:200]
                    if keywords:
                        urgent.append({
                            "text": truncated,
                            "time": msg["time"],
                            "keywords": keywords,
                        })
                        # Accumulate keyword counts
                        for kw in keywords:
                            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
                    else:
                        if len(recent_non_urgent) < 5:
                            recent_non_urgent.append({
                                "text": truncated,
                                "time": msg["time"],
                            })

                total_messages += len(messages)
                urgent_messages += len(urgent)

                channels_output[channel_id] = {
                    "name": channel_meta["name"],
                    "category": channel_meta["category"],
                    "messages": len(messages),
                    "latest_time": messages[0]["time"] if messages else "",
                    "urgent": urgent,
                    "recent": recent_non_urgent,
                }

                # Polite delay between requests
                if idx < len(channel_ids) - 1:
                    await asyncio.sleep(REQUEST_DELAY)

        cross_validated = _cross_validate(channels_output)

        return {
            "source": "telegram_osint",
            "channels_polled": len(self._channels) - channels_failed,
            "channels_failed": channels_failed,
            "total_messages": total_messages,
            "urgent_messages": urgent_messages,
            "channels": channels_output,
            "urgency_summary": {
                "total_urgent": urgent_messages,
                "by_keyword": keyword_counts,
                "cross_validated": cross_validated,
            },
        }

    async def execute_query(self, query: dict) -> list[dict]:
        """OSINT-compatible query interface.

        Accepts a structured query dict and delegates to fetch().

        Args:
            query: dict with optional keys:
                - type: str -- currently only "channel_scrape" (or omit)
                - params: dict -- may contain:
                    - max_messages: int (default 20)
                    - hours_back: int (default 24)
                    - channels: list[str] -- restrict to subset of channel IDs

        Returns:
            List containing a single result dict (the full fetch() output).
        """
        params = query.get("params", {}) if "params" in query else query

        max_messages = int(params.get("max_messages", 20))
        hours_back = int(params.get("hours_back", 24))

        # Optional channel subset filtering
        channel_subset = params.get("channels")
        if channel_subset:
            filtered = {k: v for k, v in self._channels.items() if k in channel_subset}
            adapter = TelegramOsintAdapter(channels=filtered)
            result = await adapter.fetch(max_messages=max_messages, hours_back=hours_back)
        else:
            result = await self.fetch(max_messages=max_messages, hours_back=hours_back)

        return [result]

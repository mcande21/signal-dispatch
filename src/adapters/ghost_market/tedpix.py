"""TEDPIX (Tehran Stock Exchange) scraper adapter.

Source: http://www.tsetmc.com/ (Tehran Stock Exchange Technology Management Company)
Auth: None (public web scraping)
TTL: 4h (compromise between market hours and daily)
"""

import asyncio
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from ..base import GhostMarketAdapter, GhostMarketApiError


class TedpixAdapter(GhostMarketAdapter):
    """TEDPIX index scraper with cache-first pattern.

    Scrapes Tehran Stock Exchange index data from tsetmc.com.
    Returns raw index data - signal interpretation handled by agent layer.
    """

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 4 hours (compromise between market hours and daily)."""
        return 14400  # 4 hours

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "tedpix"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of TEDPIX index data.

        Args:
            query: {} (no params needed)

        Returns:
            {
                "index_value": float,
                "daily_change": float,
                "daily_change_pct": float,
                "volume": float | None,
                "timestamp": str,
            }
        """
        del query  # Interface param, not used by this adapter
        cache_key = "tedpix_index"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- scrape tsetmc.com with retry for retryable errors
        try:
            data = await self._scrape_tsetmc()
        except GhostMarketApiError as e:
            if e.retryable:
                await asyncio.sleep(2)
                data = await self._scrape_tsetmc()
            else:
                raise

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _scrape_tsetmc(self) -> dict:
        """Scrape TEDPIX data from tsetmc.com.

        Tries multiple endpoints in sequence:
        1. JSON API endpoint (if available)
        2. MarketWatch HTML page
        3. Index.aspx page

        Returns:
            {
                "index_value": float,
                "daily_change": float,
                "daily_change_pct": float,
                "volume": float | None,
                "timestamp": str,
            }
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fa,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Try endpoints in sequence
        errors = []

        # Strategy 1: Try JSON API endpoint (tsev2/data/Index.aspx)
        try:
            return await self._try_json_endpoint(headers)
        except GhostMarketApiError as e:
            errors.append(f"JSON API: {e}")

        # Strategy 2: Try MarketWatch HTML page
        try:
            return await self._try_marketwatch_page(headers)
        except GhostMarketApiError as e:
            errors.append(f"MarketWatch: {e}")

        # Strategy 3: Try main Index page as last resort
        try:
            return await self._try_index_page(headers)
        except GhostMarketApiError as e:
            errors.append(f"Index page: {e}")

        # All strategies failed
        raise GhostMarketApiError(
            f"All tsetmc.com endpoints failed. Errors: {'; '.join(errors)}. "
            "Site may be unreachable due to Iran internet shutdown.",
            retryable=True
        )

    async def _try_json_endpoint(self, headers: dict) -> dict:
        """Try fetching from JSON API endpoint."""
        url = "http://www.tsetmc.com/tsev2/data/Index.aspx?i=1&t=value"

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()

                # tsetmc sometimes returns semicolon-delimited data
                text = response.text.strip()

                # Expected format: value;change;changePct;...
                parts = text.split(';')
                if len(parts) >= 3:
                    try:
                        index_value = float(parts[0].replace(',', ''))
                        daily_change = float(parts[1].replace(',', ''))
                        daily_change_pct = float(parts[2].replace(',', ''))

                        return {
                            "index_value": index_value,
                            "daily_change": daily_change,
                            "daily_change_pct": daily_change_pct,
                            "volume": None,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    except (ValueError, IndexError) as e:
                        raise GhostMarketApiError(
                            f"Failed to parse JSON API response: {e}"
                        ) from e

                raise GhostMarketApiError("JSON API returned unexpected format")

        except httpx.HTTPStatusError as e:
            raise self._handle_http_error(e, "tsetmc.com")
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to tsetmc.com (site may be blocked/down)", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "tsetmc.com request timed out", retryable=True
            ) from e

    async def _try_marketwatch_page(self, headers: dict) -> dict:
        """Try scraping from MarketWatch HTML page."""
        url = "http://www.tsetmc.com/Loader.aspx?ParTree=15131F"

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                html = response.text

        except httpx.HTTPStatusError as e:
            raise self._handle_http_error(e, "tsetmc.com")
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise GhostMarketApiError(
                "Cannot reach tsetmc.com MarketWatch page", retryable=True
            ) from e

        # Parse HTML for index data
        try:
            soup = BeautifulSoup(html, "html.parser")

            # tsetmc uses various patterns - try multiple selectors
            # Look for TEDPIX in tables or divs with Persian text "شاخص کل"

            # Strategy: Find script tags with embedded JSON data
            script_tags = soup.find_all("script")
            for script in script_tags:
                script_content = script.string
                if script_content and ("Overall" in script_content or "شاخص" in script_content):
                    # Try to extract numbers from JavaScript
                    numbers = re.findall(r'[-+]?\d+\.?\d*', script_content)
                    if len(numbers) >= 3:
                        try:
                            # First large number is likely the index
                            candidates = [float(n) for n in numbers if float(n) > 1000000]
                            if candidates:
                                return {
                                    "index_value": candidates[0],
                                    "daily_change": 0.0,
                                    "daily_change_pct": 0.0,
                                    "volume": None,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                }
                        except (ValueError, IndexError):
                            continue

            raise GhostMarketApiError(
                "Could not find TEDPIX data in MarketWatch page HTML"
            )

        except (ValueError, AttributeError) as e:
            raise GhostMarketApiError(
                f"Failed to parse MarketWatch HTML: {e}"
            ) from e

    async def _try_index_page(self, headers: dict) -> dict:
        """Try scraping from main index page."""
        # TEDPIX overall index has a specific instrument code
        # This is a common code but may need adjustment
        url = "http://www.tsetmc.com/Loader.aspx?ParTree=151311&i=32097828799138957"

        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                html = response.text

        except httpx.HTTPStatusError as e:
            raise self._handle_http_error(e, "tsetmc.com")
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise GhostMarketApiError(
                "Cannot reach tsetmc.com index page", retryable=True
            ) from e

        # Parse HTML
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Look for price elements - tsetmc uses various id/class patterns
            # Try common patterns
            price_elem = (
                soup.find("div", id="LastValue") or
                soup.find("span", id="LastValue") or
                soup.find("div", id="PDrCotVal") or
                soup.find("span", id="PDrCotVal") or
                soup.find("div", class_="LastValue") or
                soup.find("span", class_="LastValue")
            )

            if not price_elem:
                raise GhostMarketApiError(
                    "Could not find index value in HTML (price element not found)"
                )

            # Extract and clean the value
            price_text = price_elem.get_text(strip=True).replace(",", "")
            index_value = float(price_text)

            # Try to find change values
            daily_change = 0.0
            daily_change_pct = 0.0

            change_elem = (
                soup.find("div", id="Change") or
                soup.find("span", id="Change") or
                soup.find("div", id="PChange") or
                soup.find("span", id="PChange")
            )

            if change_elem:
                try:
                    change_text = change_elem.get_text(strip=True).replace(",", "")
                    change_text = "".join(c for c in change_text if c.isdigit() or c in "+-.")
                    if change_text and change_text not in ["+", "-", "."]:
                        daily_change = float(change_text)
                except (ValueError, AttributeError):
                    pass

            return {
                "index_value": index_value,
                "daily_change": daily_change,
                "daily_change_pct": daily_change_pct,
                "volume": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except (ValueError, AttributeError) as e:
            raise GhostMarketApiError(
                f"Failed to parse index page HTML: {e}"
            ) from e

    def _handle_http_error(self, error: httpx.HTTPStatusError, site: str) -> GhostMarketApiError:
        """Convert HTTP errors to GhostMarketApiError."""
        status_code = error.response.status_code
        if status_code == 403:
            return GhostMarketApiError(
                f"{site} blocked request (403)", status_code=403
            )
        elif status_code == 404:
            return GhostMarketApiError(
                f"{site} endpoint not found (404)", status_code=404
            )
        elif status_code == 429:
            return GhostMarketApiError(
                f"{site} rate limit exceeded", status_code=429, retryable=True
            )
        elif 500 <= status_code < 600:
            return GhostMarketApiError(
                f"{site} server error: {status_code}",
                status_code=status_code,
                retryable=True,
            )
        else:
            return GhostMarketApiError(
                f"{site} HTTP error: {status_code}", status_code=status_code
            )

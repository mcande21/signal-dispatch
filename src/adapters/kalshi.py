"""Kalshi prediction market API adapter.

Fetches YES prices for tracked geopolitical markets.

Source: https://api.elections.kalshi.com/trade-api/v2
Auth: RSA-PSS signing (KALSHI_KEY_ID + KALSHI_PRIVATE_KEY_PATH env vars)
TTL: 30 minutes
"""

import base64
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import httpx

from .base import GhostMarketAdapter, GhostMarketApiError


KALSHI_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"


def _sign_request(key_id: str, private_key, method: str, url: str) -> dict[str, str]:
    """Generate Kalshi RSA-PSS auth headers for a request."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    timestamp_ms = str(int(time.time() * 1000))
    path = urlparse(url).path if url.startswith("http") else url.split("?")[0]
    message = f"{timestamp_ms}{method.upper()}{path}".encode("utf-8")

    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )

    return {
        "KALSHI-ACCESS-KEY": key_id,
        "KALSHI-ACCESS-SIGNATURE": base64.b64encode(signature).decode("utf-8"),
        "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
    }


def _load_private_key(path: str):
    """Load RSA private key from PEM file."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    with open(Path(path).expanduser(), "rb") as f:
        key = serialization.load_pem_private_key(f.read(), password=None)
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValueError("KALSHI_PRIVATE_KEY_PATH must point to an RSA private key")
    return key


class KalshiAdapter(GhostMarketAdapter):
    """Kalshi prediction market adapter with cache-first pattern.

    Fetches current YES prices for specified market tickers.
    Returns raw market data -- signal interpretation handled by agent layer.

    Auth: RSA-PSS via KALSHI_KEY_ID + KALSHI_PRIVATE_KEY_PATH environment variables.
    """

    def __init__(self, db_path: str):
        super().__init__(db_path)
        self.key_id = os.environ.get("KALSHI_KEY_ID")
        key_path = os.environ.get("KALSHI_PRIVATE_KEY_PATH")
        self._private_key = None
        if self.key_id and key_path:
            try:
                self._private_key = _load_private_key(key_path)
            except Exception as e:
                # Non-fatal: adapter will fail gracefully on fetch
                import logging
                logging.getLogger(__name__).warning(
                    "KalshiAdapter: could not load private key from %s: %s", key_path, e
                )

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 30 minutes."""
        return 1800

    @property
    def source_name(self) -> str:
        return "kalshi"

    def _auth_headers(self, method: str, url: str) -> dict[str, str]:
        """Build auth headers. Raises GhostMarketApiError if not configured."""
        if not self.key_id or not self._private_key:
            raise GhostMarketApiError(
                "Kalshi auth not configured: set KALSHI_KEY_ID and KALSHI_PRIVATE_KEY_PATH",
                retryable=False,
            )
        return _sign_request(self.key_id, self._private_key, method, url)

    async def fetch(self, query: dict) -> dict:
        """Fetch current YES prices for a list of Kalshi market tickers.

        Args:
            query: {
                "tickers": list[str]   -- e.g. ["KXCLOSEHORMUZ", "KXIRANISR"]
            }

        Returns:
            {
                "markets": {
                    "<ticker>": {
                        "ticker": str,
                        "title": str,
                        "yes_bid": float,     -- 0.0-1.0
                        "yes_ask": float,     -- 0.0-1.0
                        "yes_price": float,   -- midpoint
                        "volume": float,
                        "open_interest": float,
                        "status": str,
                    }
                },
                "fetched_at": str
            }
        """
        tickers = query.get("tickers", [])
        if not tickers:
            raise GhostMarketApiError("kalshi: 'tickers' parameter required")

        cache_key = "markets_" + "_".join(sorted(tickers))
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        markets: dict = {}
        for ticker in tickers:
            try:
                market_data = await self._fetch_market(ticker)
                markets[ticker] = market_data
            except GhostMarketApiError as e:
                markets[ticker] = {
                    "ticker": ticker,
                    "title": ticker,
                    "yes_bid": None,
                    "yes_ask": None,
                    "yes_price": None,
                    "volume": None,
                    "open_interest": None,
                    "status": "error",
                    "error": str(e),
                }

        result = {
            "markets": markets,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

        await self._cache_store(cache_key, result)
        return result

    async def _fetch_market(self, ticker: str) -> dict:
        """Fetch a single market's current price data."""
        url = f"{KALSHI_BASE_URL}/markets/{ticker}"

        try:
            headers = self._auth_headers("GET", url)
        except GhostMarketApiError:
            raise

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15.0)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            raise GhostMarketApiError(
                f"Kalshi market fetch HTTP {status_code} for {ticker}",
                status_code=status_code,
                retryable=status_code == 429 or status_code >= 500,
            ) from e
        except httpx.HTTPError as e:
            raise GhostMarketApiError(
                f"Kalshi network error for {ticker}: {e}",
                retryable=True,
            ) from e

        market = data.get("market", data)

        # YES prices come back as cents (0-100), normalize to 0.0-1.0
        yes_bid_raw = market.get("yes_bid", market.get("last_price"))
        yes_ask_raw = market.get("yes_ask", market.get("last_price"))

        def _cents_to_decimal(v) -> float | None:
            if v is None:
                return None
            try:
                f = float(v)
                # Values > 1 are in cents (0-100), normalize
                return f / 100.0 if f > 1.0 else f
            except (TypeError, ValueError):
                return None

        yes_bid = _cents_to_decimal(yes_bid_raw)
        yes_ask = _cents_to_decimal(yes_ask_raw)
        yes_price = None
        if yes_bid is not None and yes_ask is not None:
            yes_price = (yes_bid + yes_ask) / 2.0
        elif yes_bid is not None:
            yes_price = yes_bid
        elif yes_ask is not None:
            yes_price = yes_ask

        return {
            "ticker": ticker,
            "title": market.get("title", ticker),
            "yes_bid": yes_bid,
            "yes_ask": yes_ask,
            "yes_price": yes_price,
            "volume": float(market.get("volume", 0) or 0),
            "open_interest": float(market.get("open_interest", 0) or 0),
            "status": market.get("status", "unknown"),
        }

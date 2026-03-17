"""Oryx war equipment loss tracking adapter.

Source: scarnecchia/oryx_data on GitHub (Oryx website scraper)
Auth: None (public repository)
TTL: 12 hours
"""

import csv
import io
from datetime import datetime, timezone

import httpx

from ..base import GhostMarketAdapter, GhostMarketApiError


# GitHub raw content URLs for Oryx CSV data
ORYX_TOTALS_URL = "https://raw.githubusercontent.com/scarnecchia/oryx_data/master/totals_by_type.csv"
ORYX_DAILY_URL = "https://raw.githubusercontent.com/scarnecchia/oryx_data/master/daily_count.csv"


class OryxAdapter(GhostMarketAdapter):
    """Oryx war equipment loss tracker with cache-first pattern.

    Fetches visually confirmed military equipment losses from Russia-Ukraine war.
    Data scraped from Oryx website and published to GitHub as CSV files.
    Returns raw loss records with basic counts. Signal interpretation by agent layer.
    """

    @property
    def ttl_seconds(self) -> int:
        """Cache TTL = 12 hours (43200 seconds)."""
        return 43200

    @property
    def source_name(self) -> str:
        """Source identifier for cache table."""
        return "oryx"

    async def fetch(self, query: dict) -> dict:
        """Cache-first fetch of Oryx equipment loss data.

        Args:
            query: {
                "dataset": str ("totals" or "daily", default "totals"),
                "country": str (optional -- "Russia" or "Ukraine" to filter, default both)
            }

        Returns (for "totals"):
            {
                "source": "oryx",
                "dataset": "totals",
                "country_filter": str (country or "all"),
                "record_count": int,
                "equipment": [
                    {
                        "country": str,
                        "equipment_type": str,
                        "destroyed": int,
                        "captured": int,
                        "abandoned": int,
                        "damaged": int,
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp)
            }

        Returns (for "daily"):
            {
                "source": "oryx",
                "dataset": "daily",
                "country_filter": str (country or "all"),
                "record_count": int,
                "daily_losses": [
                    {
                        "date": str (YYYY-MM-DD),
                        "country": str,
                        "total": int,
                        "destroyed": int,
                        "captured": int,
                        "abandoned": int,
                        "damaged": int,
                    },
                    ...
                ],
                "fetched_at": str (ISO timestamp)
            }
        """
        # Extract parameters
        dataset = query.get("dataset", "totals")
        country_filter = query.get("country")

        # Validate dataset
        if dataset not in ("totals", "daily"):
            raise GhostMarketApiError(
                f"oryx: 'dataset' must be 'totals' or 'daily', got '{dataset}'"
            )

        # Normalize country filter (case-insensitive)
        if country_filter:
            country_filter = country_filter.strip().title()
            if country_filter not in ("Russia", "Ukraine"):
                raise GhostMarketApiError(
                    f"oryx: 'country' must be 'Russia' or 'Ukraine', got '{country_filter}'"
                )

        # Build cache key
        cache_key = f"{dataset}_{country_filter or 'all'}"

        # 1. Check cache
        cached = await self._cache_lookup(cache_key)
        if cached:
            return cached

        # 2. Cache miss -- fetch from GitHub
        data = await self._fetch_github_csv(dataset, country_filter)

        # 3. Cache the result
        await self._cache_store(cache_key, data)

        return data

    async def _fetch_github_csv(self, dataset: str, country_filter: str | None) -> dict:
        """Fetch and parse CSV data from GitHub repository.

        Args:
            dataset: "totals" or "daily"
            country_filter: None (all countries), "Russia", or "Ukraine"

        Returns:
            Structured dict with parsed CSV records
        """
        # Select URL based on dataset
        url = ORYX_TOTALS_URL if dataset == "totals" else ORYX_DAILY_URL

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                csv_data = response.text

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code == 404:
                raise GhostMarketApiError(
                    "Oryx GitHub repository not found (404)",
                    status_code=404,
                    retryable=False,
                ) from e
            elif status_code == 429:
                raise GhostMarketApiError(
                    "GitHub rate limit exceeded",
                    status_code=429,
                    retryable=True,
                ) from e
            elif 500 <= status_code < 600:
                raise GhostMarketApiError(
                    f"GitHub server error: {status_code}",
                    status_code=status_code,
                    retryable=True,
                ) from e
            else:
                raise GhostMarketApiError(
                    f"GitHub HTTP error: {status_code}",
                    status_code=status_code,
                ) from e
        except httpx.ConnectError as e:
            raise GhostMarketApiError(
                "Cannot connect to GitHub", retryable=True
            ) from e
        except httpx.TimeoutException as e:
            raise GhostMarketApiError(
                "GitHub request timed out", retryable=True
            ) from e

        # Parse CSV
        if dataset == "totals":
            records = self._parse_totals_csv(csv_data, country_filter)
            return {
                "source": "oryx",
                "dataset": "totals",
                "country_filter": country_filter or "all",
                "record_count": len(records),
                "equipment": records,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        else:  # daily
            records = self._parse_daily_csv(csv_data, country_filter)
            return {
                "source": "oryx",
                "dataset": "daily",
                "country_filter": country_filter or "all",
                "record_count": len(records),
                "daily_losses": records,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

    def _parse_totals_csv(self, csv_data: str, country_filter: str | None) -> list[dict]:
        """Parse totals_by_type.csv into equipment records.

        CSV columns: country, equipment_type, destroyed, captured, abandoned,
                     damaged, damaged_and_abandoned, damaged_and_captured

        Returns list of dicts with country, equipment_type, and loss counts.
        """
        records = []
        reader = csv.DictReader(io.StringIO(csv_data))

        for row in reader:
            country = row.get("country", "").strip()

            # Apply country filter if specified
            if country_filter and country != country_filter:
                continue

            # Safe int parsing
            def parse_int(val: str | None) -> int:
                if val is None or val == "":
                    return 0
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0

            record = {
                "country": country,
                "equipment_type": row.get("equipment_type", "").strip(),
                "destroyed": parse_int(row.get("destroyed")),
                "captured": parse_int(row.get("captured")),
                "abandoned": parse_int(row.get("abandoned")),
                "damaged": parse_int(row.get("damaged")),
            }
            records.append(record)

        return records

    def _parse_daily_csv(self, csv_data: str, country_filter: str | None) -> list[dict]:
        """Parse daily_count.csv into time series records.

        CSV columns: date, country, total_losses, destroyed, captured,
                     abandoned, damaged

        Returns list of dicts with date, country, and daily loss counts.
        """
        records = []
        reader = csv.DictReader(io.StringIO(csv_data))

        for row in reader:
            country = row.get("country", "").strip()

            # Apply country filter if specified
            if country_filter and country != country_filter:
                continue

            # Safe int parsing
            def parse_int(val: str | None) -> int:
                if val is None or val == "":
                    return 0
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return 0

            record = {
                "date": row.get("date", "").strip(),
                "country": country,
                "total": parse_int(row.get("total_losses")),
                "destroyed": parse_int(row.get("destroyed")),
                "captured": parse_int(row.get("captured")),
                "abandoned": parse_int(row.get("abandoned")),
                "damaged": parse_int(row.get("damaged")),
            }
            records.append(record)

        return records

#!/usr/bin/env python3
"""
Migration: normalize legacy 'gdelt' source rows to per-query source keys.

Old format: source='gdelt', payload contains query='Iran military conflict'
New format: source='gdelt_iran_military_conflict'

The query string is already in the payload for all rows — this migration
just makes source consistent so analytics/alerting can query a single key.

Safe to run multiple times (idempotent — skips rows already migrated).
"""

import sqlite3
import json
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "signals.db"


def query_to_source_key(query: str) -> str:
    """Convert a GDELT query string to a normalized source key.

    'Iran military conflict' -> 'gdelt_iran_military_conflict'
    'Strait Hormuz Iran'     -> 'gdelt_strait_hormuz_iran'
    """
    slug = re.sub(r"[^a-z0-9]+", "_", query.strip().lower()).strip("_")
    return f"gdelt_{slug}"


def run_migration(dry_run: bool = False) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Fetch all legacy rows
    cur.execute(
        "SELECT id, source, payload FROM source_readings WHERE source = 'gdelt'"
    )
    rows = cur.fetchall()
    print(f"Found {len(rows)} legacy 'gdelt' rows to migrate.")

    updates = []
    skipped = 0
    for row_id, source, payload_json in rows:
        try:
            payload = json.loads(payload_json) if payload_json else {}
        except json.JSONDecodeError:
            print(f"  WARN: row {row_id} has unparseable payload, skipping")
            skipped += 1
            continue

        query = payload.get("query", "").strip()
        if not query:
            print(f"  WARN: row {row_id} has no query in payload, skipping")
            skipped += 1
            continue

        new_source = query_to_source_key(query)
        updates.append((new_source, row_id, query))

    print(f"\nMigration plan ({len(updates)} rows, {skipped} skipped):")
    # Show summary by new key
    by_key: dict[str, int] = {}
    for new_source, row_id, query in updates:
        by_key[new_source] = by_key.get(new_source, 0) + 1
    for key, count in sorted(by_key.items()):
        print(f"  gdelt -> {key}: {count} rows")

    if dry_run:
        print("\n[DRY RUN] No changes written.")
        conn.close()
        return

    # Apply updates
    for new_source, row_id, query in updates:
        cur.execute(
            "UPDATE source_readings SET source = ? WHERE id = ?",
            (new_source, row_id),
        )

    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM source_readings WHERE source = 'gdelt'")
    remaining = cur.fetchone()[0]
    cur.execute(
        "SELECT source, COUNT(*) FROM source_readings WHERE source LIKE 'gdelt_%' GROUP BY source ORDER BY source"
    )
    after = cur.fetchall()

    print(f"\nDone. Remaining legacy 'gdelt' rows: {remaining}")
    print("Per-query source counts after migration:")
    for src, count in after:
        print(f"  {src}: {count}")

    conn.close()


if __name__ == "__main__":
    import sys
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN ===")
    run_migration(dry_run=dry_run)

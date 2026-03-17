"""Cluster detection -- correlate deltas by geographic/thematic association.

A cluster fires when 3+ sources in the same group breach thresholds within
a 72-hour window and all point in the same adverse direction.

Cluster groups are defined below. Each source can belong to multiple groups.
Cluster output is written to content/state/deltas/clusters/latest.json.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Cluster group definitions
# ---------------------------------------------------------------------------

CLUSTER_GROUPS: dict[str, dict] = {
    "iran": {
        "label": "Iran Stress Cluster",
        "description": "Correlated signals suggesting elevated Iranian regime stress or military posture",
        "sources": ["bonbast", "ooni", "tedpix", "gdelt", "prediction_markets"],
        "theme": "geopolitical",
    },
    "hormuz": {
        "label": "Strait of Hormuz Risk Cluster",
        "description": "Correlated signals indicating elevated Hormuz closure risk",
        "sources": ["bonbast", "ooni", "eia", "gdelt", "prediction_markets"],
        "theme": "geopolitical",
    },
    "europe_energy": {
        "label": "Europe Energy Cluster",
        "description": "Correlated signals indicating European energy market stress",
        "sources": ["agsi", "entsog", "gdelt", "ecb"],
        "theme": "energy",
    },
    "conflict": {
        "label": "Active Conflict Cluster",
        "description": "Correlated signals from active conflict zones",
        "sources": ["gdelt", "viirs", "oryx", "prediction_markets"],
        "theme": "conflict",
    },
    "us_macro": {
        "label": "US Macro Stress Cluster",
        "description": "Correlated US macroeconomic stress signals",
        "sources": ["fred", "eia", "prediction_markets"],
        "theme": "macro",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_adverse(delta: dict) -> bool:
    """Return True if a delta is in the adverse/alarming direction."""
    status = delta.get("threshold_status", "clear")
    if status not in ("watch", "breached"):
        return False

    delta_type = delta.get("delta_type", "")
    d = delta.get("delta", {})

    if delta_type == "numeric":
        # Adverse = percent change was flagged by threshold eval
        # Threshold eval already handles direction implicitly (abs check)
        return True
    elif delta_type == "event_set":
        # Adverse = count going up (more events)
        return d.get("absolute", 0) > 0
    elif delta_type == "binary":
        # Adverse = state activated (True = anomaly/blocking)
        curr = delta.get("current", {})
        return bool(curr.get("state", False))
    elif delta_type == "categorical":
        # Adverse = entries were added (sanctions additions, new regulations)
        return d.get("added_count", 0) > 0

    return True  # unknown type -- assume adverse


def _within_window_hours(timestamp_iso: str, window_hours: int = 72) -> bool:
    """Return True if timestamp is within the past window_hours."""
    try:
        ts = datetime.fromisoformat(timestamp_iso)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta_hours = (now - ts).total_seconds() / 3600
        return delta_hours <= window_hours
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def detect_clusters(
    deltas: list[dict],
    thresholds: dict,
    window_hours: int = 72,
) -> list[dict]:
    """Detect correlated clusters from a list of delta results.

    Args:
        deltas: List of delta dicts (output of engine.compute_*)
        thresholds: Loaded thresholds.yaml content
        window_hours: Time window for correlation (default 72h)

    Returns:
        List of cluster dicts. Empty if no clusters detected.
    """
    cluster_cfg = thresholds.get("cluster", {})
    min_sources_notification = cluster_cfg.get("notification", {}).get("min_sources", 3)
    min_sources_watch = cluster_cfg.get("watch", {}).get("min_sources", 2)

    # Index deltas by source name (take highest-severity if multiple per source)
    by_source: dict[str, dict] = {}
    for d in deltas:
        src = d.get("source", "")
        if src not in by_source:
            by_source[src] = d
        else:
            # Prefer breached > watch > clear
            existing_status = by_source[src].get("threshold_status", "clear")
            new_status = d.get("threshold_status", "clear")
            severity_rank = {"breached": 2, "watch": 1, "clear": 0}
            if severity_rank.get(new_status, 0) > severity_rank.get(existing_status, 0):
                by_source[src] = d

    detected: list[dict] = []

    for group_id, group_def in CLUSTER_GROUPS.items():
        group_sources = group_def["sources"]
        triggered: list[dict] = []

        for src in group_sources:
            d = by_source.get(src)
            if d is None:
                continue
            status = d.get("threshold_status", "clear")
            if status not in ("watch", "breached"):
                continue
            ts = d.get("timestamp", "")
            if ts and not _within_window_hours(ts, window_hours):
                continue
            triggered.append(d)

        if len(triggered) < min_sources_watch:
            continue

        # Check all-same-direction for notification level
        adverse_triggered = [t for t in triggered if _is_adverse(t)]
        all_adverse = len(adverse_triggered) == len(triggered)

        if len(triggered) >= min_sources_notification:
            cluster_status = "breached" if all_adverse else "watch"
        else:
            cluster_status = "watch"

        # Build summary
        source_summaries = [
            {
                "source": t.get("source"),
                "threshold_status": t.get("threshold_status"),
                "plain_english": t.get("plain_english", ""),
            }
            for t in triggered
        ]

        plain = (
            f"{group_def['label']}: {len(triggered)} sources breached within {window_hours}h "
            f"({'all adverse' if all_adverse else 'mixed direction'}). "
            f"Sources: {', '.join(t.get('source', '') for t in triggered)}."
        )

        detected.append({
            "cluster_id": group_id,
            "label": group_def["label"],
            "description": group_def["description"],
            "theme": group_def["theme"],
            "timestamp": _now_iso(),
            "window_hours": window_hours,
            "status": cluster_status,
            "triggered_count": len(triggered),
            "all_adverse": all_adverse,
            "source_summaries": source_summaries,
            "plain_english": plain,
        })

    return detected


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def write_clusters(clusters: list[dict], clusters_dir: Path) -> Path:
    """Atomically write cluster results to clusters/latest.json.

    Args:
        clusters: Output of detect_clusters()
        clusters_dir: Path to content/state/deltas/clusters/

    Returns:
        Path to written file.
    """
    clusters_dir.mkdir(parents=True, exist_ok=True)
    out_path = clusters_dir / "latest.json"

    payload = {
        "generated_at": _now_iso(),
        "cluster_count": len(clusters),
        "clusters": clusters,
    }

    _atomic_write(out_path, payload)
    return out_path


def _atomic_write(path: Path, data: Any) -> None:
    """Write JSON atomically: write .tmp, rename over target."""
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(path.parent), prefix=path.name, suffix=".tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

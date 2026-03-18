"""Delta merge -- aggregate accumulated deltas since last published issue.

Reads delta history, clusters, and alerts from content/state/deltas/ and
produces a structured delta_summary.md for use as Phase 0 input in /intel.

Usage (CLI):
    .venv/bin/python -m src.delta.merge --issue 5 --output content/research/5/delta_summary.md

Usage (Python):
    from src.delta.merge import generate_delta_summary
    path = generate_delta_summary(issue_number=5, output_path="content/research/5/delta_summary.md")
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_SD_ROOT = Path(__file__).parent.parent.parent
_ISSUES_PATH = _SD_ROOT / "content" / "state" / "issues.json"
_DELTAS_ROOT = _SD_ROOT / "content" / "state" / "deltas"
_HISTORY_DIR = _DELTAS_ROOT / "history"
_CLUSTERS_DIR = _DELTAS_ROOT / "clusters"
_ALERTS_PENDING_DIR = _DELTAS_ROOT / "alerts" / "pending"
_ALERTS_ACKED_DIR = _DELTAS_ROOT / "alerts" / "acknowledged"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("delta.merge")

# ---------------------------------------------------------------------------
# Source cadence / theme groupings
# ---------------------------------------------------------------------------

# Cadence tiers -- mirrors daemon.py cadence definitions
HOT_SOURCES = frozenset([
    "bonbast", "ooni", "cloudflare_radar", "tedpix",
    "dolarvzla", "gdelt", "viirs", "prediction_markets",
])
WARM_SOURCES = frozenset([
    "eia", "agsi", "entsog", "ofac", "oryx",
    "usaspending", "federal_register", "congress",
])
COLD_SOURCES = frozenset([
    "fred", "ecb", "comtrade", "eia_grid", "fec", "noaa",
])

# Theme groupings for hot sources -- matches clusters.py conceptual groupings
# Keys are display names; values are source name prefixes that map to this theme.
HOT_THEMES: dict[str, list[str]] = {
    "Iran Cluster": ["bonbast", "ooni", "cloudflare_radar", "tedpix"],
    "Conflict": ["gdelt", "viirs"],
    "Markets": ["prediction_markets", "dolarvzla"],
}

# Severity sort order
_SEVERITY_RANK: dict[str, int] = {"breached": 2, "watch": 1, "clear": 0}

# Severity emoji / label for display
_SEVERITY_LABEL: dict[str, str] = {
    "breached": "BREACHED",
    "watch": "WATCH",
    "clear": "clear",
}


# ---------------------------------------------------------------------------
# Issues.json helpers
# ---------------------------------------------------------------------------

def _load_issues() -> dict:
    if not _ISSUES_PATH.exists():
        raise FileNotFoundError(f"issues.json not found at {_ISSUES_PATH}")
    with open(_ISSUES_PATH) as f:
        return json.load(f)


def _last_published_issue(issues_data: dict) -> tuple[int, str] | tuple[None, None]:
    """Return (issue_number, published_date) of the most recent published issue.

    Returns (None, None) if no published issues exist.
    """
    published = [
        i for i in issues_data.get("issues", [])
        if i.get("status") == "published" and i.get("published_date")
    ]
    if not published:
        return None, None
    latest = max(published, key=lambda i: i["published_date"])
    return latest["issue_number"], latest["published_date"]


# ---------------------------------------------------------------------------
# History scanning
# ---------------------------------------------------------------------------

def _parse_date_from_iso(ts: str) -> date | None:
    """Parse an ISO timestamp string into a date. Returns None on failure."""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.date()
    except (ValueError, TypeError):
        return None


def _load_deltas_since(since_date: date) -> list[dict]:
    """Scan all JSONL history files and return deltas with timestamp >= since_date.

    Deduplicates: for each source, keeps the most severe entry from each day.
    Returns a flat list sorted by timestamp descending.
    """
    if not _HISTORY_DIR.exists():
        log.warning("History directory does not exist: %s", _HISTORY_DIR)
        return []

    collected: list[dict] = []

    for jsonl_file in sorted(_HISTORY_DIR.glob("*.jsonl")):
        # Filename format: {source}-{YYYY-MM-DD}.jsonl
        stem = jsonl_file.stem
        # Extract date portion: last 10 chars are YYYY-MM-DD
        try:
            file_date = date.fromisoformat(stem[-10:])
        except ValueError:
            log.debug("Could not parse date from filename: %s", jsonl_file.name)
            continue

        if file_date < since_date:
            continue

        try:
            with open(jsonl_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        collected.append(entry)
                    except json.JSONDecodeError:
                        log.debug("Skipping malformed line in %s", jsonl_file.name)
        except OSError as e:
            log.warning("Could not read %s: %s", jsonl_file, e)

    # Sort by timestamp descending (most recent first)
    collected.sort(
        key=lambda d: d.get("timestamp", ""),
        reverse=True,
    )
    return collected


def _deduplicate_by_source(deltas: list[dict]) -> list[dict]:
    """For each source, keep only the highest-severity delta.

    If two entries share the same source and severity, keep the more recent one.
    The input list is assumed to be sorted descending by timestamp.
    """
    seen: dict[str, dict] = {}
    for delta in deltas:
        src = delta.get("source", "unknown")
        if src not in seen:
            seen[src] = delta
        else:
            existing_rank = _SEVERITY_RANK.get(seen[src].get("threshold_status", "clear"), 0)
            new_rank = _SEVERITY_RANK.get(delta.get("threshold_status", "clear"), 0)
            if new_rank > existing_rank:
                seen[src] = delta
    return list(seen.values())


# ---------------------------------------------------------------------------
# Clusters
# ---------------------------------------------------------------------------

def _load_clusters() -> list[dict]:
    """Load active clusters from clusters/latest.json. Returns [] if missing."""
    latest = _CLUSTERS_DIR / "latest.json"
    if not latest.exists():
        return []
    try:
        with open(latest) as f:
            payload = json.load(f)
        return payload.get("clusters", [])
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Could not load clusters: %s", e)
        return []


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

def _load_alerts_since(since_date: date) -> tuple[list[dict], list[dict]]:
    """Load pending and acknowledged alerts created on or after since_date.

    Returns (pending_alerts, acknowledged_alerts).
    """
    def _scan_dir(alert_dir: Path) -> list[dict]:
        if not alert_dir.exists():
            return []
        results: list[dict] = []
        for f in sorted(alert_dir.glob("*.json")):
            try:
                with open(f) as fh:
                    payload = json.load(fh)
                created = payload.get("created_at", "")
                created_date = _parse_date_from_iso(created)
                if created_date is None or created_date < since_date:
                    continue
                results.append(payload)
            except (json.JSONDecodeError, OSError) as e:
                log.debug("Skipping alert file %s: %s", f, e)
        return results

    pending = _scan_dir(_ALERTS_PENDING_DIR)
    acknowledged = _scan_dir(_ALERTS_ACKED_DIR)
    return pending, acknowledged


# ---------------------------------------------------------------------------
# Source theme classification
# ---------------------------------------------------------------------------

def _classify_source(source_name: str) -> str:
    """Return cadence tier for a source name: 'hot', 'warm', or 'cold'."""
    # Strip prefixes like "gdelt_iran", "viirs_ir", "pm_KXFED"
    base = source_name.split("_")[0]
    if base in HOT_SOURCES or source_name in HOT_SOURCES:
        return "hot"
    if base in WARM_SOURCES or source_name in WARM_SOURCES:
        return "warm"
    if base in COLD_SOURCES or source_name in COLD_SOURCES:
        return "cold"
    # Prediction market tickers start with "pm_"
    if source_name.startswith("pm_"):
        return "hot"
    # Fred variants like "fred_vixcls"
    if source_name.startswith("fred_"):
        return "cold"
    # EIA variants like "eia_wcestus1"
    if source_name.startswith("eia_"):
        return "warm"
    # AGSI/VIIRS variants
    if source_name.startswith("agsi_") or source_name.startswith("viirs_"):
        return "hot" if source_name.startswith("viirs_") else "warm"
    if source_name.startswith("oryx_"):
        return "warm"
    if source_name.startswith("gdelt_"):
        return "hot"
    return "cold"


def _source_matches_theme(source_name: str, theme_sources: list[str]) -> bool:
    """Return True if source_name starts with any of the theme source prefixes."""
    for ts in theme_sources:
        if source_name == ts or source_name.startswith(ts + "_"):
            return True
    return False


def _group_hot_by_theme(hot_deltas: list[dict]) -> dict[str, list[dict]]:
    """Bucket hot deltas into HOT_THEMES groups. Unmatched go into 'Other'."""
    groups: dict[str, list[dict]] = {theme: [] for theme in HOT_THEMES}
    groups["Other"] = []

    for delta in hot_deltas:
        src = delta.get("source", "")
        matched = False
        for theme, theme_sources in HOT_THEMES.items():
            if _source_matches_theme(src, theme_sources):
                groups[theme].append(delta)
                matched = True
                break
        if not matched:
            groups["Other"].append(delta)

    return groups


# ---------------------------------------------------------------------------
# Markdown formatting helpers
# ---------------------------------------------------------------------------

def _severity_badge(status: str) -> str:
    return _SEVERITY_LABEL.get(status, status.upper())


def _format_delta_line(delta: dict) -> str:
    """Format a single delta as a bullet line using plain_english description."""
    src = delta.get("source", "unknown")
    status = delta.get("threshold_status", "clear")
    plain = delta.get("plain_english", "(no description)")
    ts = delta.get("timestamp", "")[:16].replace("T", " ")  # YYYY-MM-DD HH:MM
    badge = _severity_badge(status)
    return f"- **[{badge}]** `{src}` ({ts}): {plain}"


def _sort_deltas_by_severity(deltas: list[dict]) -> list[dict]:
    """Sort descending by severity: breached > watch > clear."""
    return sorted(
        deltas,
        key=lambda d: _SEVERITY_RANK.get(d.get("threshold_status", "clear"), 0),
        reverse=True,
    )


def _partition_by_threshold(
    deltas: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Partition deltas into (breached, watch, clear) lists."""
    breached = [d for d in deltas if d.get("threshold_status") == "breached"]
    watch = [d for d in deltas if d.get("threshold_status") == "watch"]
    clear = [d for d in deltas if d.get("threshold_status", "clear") == "clear"]
    return breached, watch, clear


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_clusters_section(clusters: list[dict]) -> str:
    if not clusters:
        return "_No active clusters detected._\n"

    lines: list[str] = []
    for cluster in clusters:
        status = cluster.get("status", "clear")
        label = cluster.get("label", cluster.get("cluster_id", "unknown"))
        plain = cluster.get("plain_english", "")
        theme = cluster.get("theme", "")
        triggered_count = cluster.get("triggered_count", 0)
        badge = _severity_badge(status)

        lines.append(f"### [{badge}] {label}")
        if theme:
            lines.append(f"**Theme:** {theme} | **Triggered sources:** {triggered_count}")
        lines.append("")
        if plain:
            lines.append(plain)
            lines.append("")

        source_summaries = cluster.get("source_summaries", [])
        if source_summaries:
            for ss in source_summaries:
                ss_status = ss.get("threshold_status", "clear")
                ss_src = ss.get("source", "")
                ss_plain = ss.get("plain_english", "")
                lines.append(f"- **[{_severity_badge(ss_status)}]** `{ss_src}`: {ss_plain}")
            lines.append("")

    return "\n".join(lines)


def _build_alerts_section(
    pending: list[dict],
    acknowledged: list[dict],
    since_date: date,
) -> str:
    all_alerts = pending + acknowledged
    if not all_alerts:
        return f"_No alerts since {since_date}._\n"

    lines: list[str] = []

    if pending:
        lines.append(f"**{len(pending)} pending alert(s) -- not yet acknowledged:**")
        lines.append("")
        for alert in sorted(pending, key=lambda a: a.get("created_at", ""), reverse=True):
            src = alert.get("source", "unknown")
            status = alert.get("threshold_status", "unknown")
            plain = alert.get("plain_english", "")
            created = alert.get("created_at", "")[:16].replace("T", " ")
            badge = _severity_badge(status)
            lines.append(f"- **[{badge}]** `{src}` at {created}: {plain}")
        lines.append("")

    if acknowledged:
        lines.append(f"**{len(acknowledged)} acknowledged alert(s):**")
        lines.append("")
        for alert in sorted(acknowledged, key=lambda a: a.get("created_at", ""), reverse=True):
            src = alert.get("source", "unknown")
            status = alert.get("threshold_status", "unknown")
            plain = alert.get("plain_english", "")
            created = alert.get("created_at", "")[:16].replace("T", " ")
            badge = _severity_badge(status)
            lines.append(f"- **[{badge}]** `{src}` at {created}: {plain}")
        lines.append("")

    return "\n".join(lines)


def _build_hot_section(hot_deltas: list[dict]) -> str:
    if not hot_deltas:
        return "_No hot-cadence deltas in window._\n"

    grouped = _group_hot_by_theme(hot_deltas)
    lines: list[str] = []

    for theme_name, theme_deltas in grouped.items():
        if not theme_deltas:
            continue
        sorted_deltas = _sort_deltas_by_severity(theme_deltas)
        lines.append(f"### {theme_name}")
        lines.append("")
        for delta in sorted_deltas:
            lines.append(_format_delta_line(delta))
        lines.append("")

    return "\n".join(lines) if lines else "_No hot-cadence deltas in window._\n"


def _build_cadence_section(deltas: list[dict], label: str) -> str:
    if not deltas:
        return f"_No {label.lower()} deltas in window._\n"

    sorted_deltas = _sort_deltas_by_severity(deltas)
    lines: list[str] = []
    for delta in sorted_deltas:
        lines.append(_format_delta_line(delta))

    return "\n".join(lines) + "\n"


def _build_no_significant_section(clear_deltas: list[dict]) -> str:
    if not clear_deltas:
        return "_All sources produced significant signals (nothing in clear)._\n"

    source_names = sorted(set(d.get("source", "unknown") for d in clear_deltas))
    items = [f"`{s}`" for s in source_names]
    return "Sources with no threshold breaches: " + ", ".join(items) + "\n"


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_delta_summary(
    issue_number: int | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """Generate delta_summary.md for the given issue.

    Args:
        issue_number: Target issue number. If None, uses next_issue_number from issues.json.
        output_path: Where to write the markdown file. If None, writes to
                     content/research/{issue_number}/delta_summary.md.

    Returns:
        Path to the written file.
    """
    issues_data = _load_issues()

    # Resolve issue number
    if issue_number is None:
        issue_number = issues_data.get("next_issue_number", 0)
        log.info("No issue number specified, using next: %d", issue_number)

    # Find last published issue to establish since_date
    last_issue_num, last_published_date_str = _last_published_issue(issues_data)

    if last_published_date_str is None:
        # No published issues yet -- use a far past date to include everything
        since_date = date(2000, 1, 1)
        since_label = "all time (no prior published issue)"
        last_issue_label = "none"
    else:
        since_date = date.fromisoformat(last_published_date_str)
        since_label = last_published_date_str
        last_issue_label = f"SD #{last_issue_num}"

    log.info(
        "Generating delta summary for SD #%d (since %s / %s)",
        issue_number,
        since_label,
        last_issue_label,
    )

    # Resolve output path
    if output_path is None:
        output_path = _SD_ROOT / "content" / "research" / str(issue_number) / "delta_summary.md"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    all_deltas = _load_deltas_since(since_date)
    deduped_deltas = _deduplicate_by_source(all_deltas)
    clusters = _load_clusters()
    pending_alerts, acked_alerts = _load_alerts_since(since_date)

    log.info(
        "Loaded %d raw deltas -> %d deduplicated, %d clusters, %d pending alerts, %d acked alerts",
        len(all_deltas),
        len(deduped_deltas),
        len(clusters),
        len(pending_alerts),
        len(acked_alerts),
    )

    # Partition by cadence
    hot_deltas = [d for d in deduped_deltas if _classify_source(d.get("source", "")) == "hot"]
    warm_deltas = [d for d in deduped_deltas if _classify_source(d.get("source", "")) == "warm"]
    cold_deltas = [d for d in deduped_deltas if _classify_source(d.get("source", "")) == "cold"]

    # Identify "no significant deltas" sources (clear threshold, all cadences)
    _, _, clear_deltas = _partition_by_threshold(deduped_deltas)

    # Emit stats for empty-state handling
    total_signals = len(deduped_deltas)
    significant = [d for d in deduped_deltas if d.get("threshold_status") in ("breached", "watch")]

    # Build the markdown
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = []

    # Header
    lines.append(f"# Delta Summary (since {last_issue_label}, {since_label})")
    lines.append("")
    lines.append(
        f"_Generated {now_utc} for SD #{issue_number}. "
        f"{total_signals} sources polled, {len(significant)} with threshold signals._"
    )
    lines.append("")
    lines.append(
        "> **Note:** This document contains raw data changes only. "
        "No probability estimates or analytical conclusions are made here. "
        "These are inputs for /intel phases that follow."
    )
    lines.append("")

    # Section: Active Clusters
    lines.append("## Active Clusters")
    lines.append("")
    lines.append(_build_clusters_section(clusters))

    # Section: Alerts
    lines.append("## Alerts Since Last Issue")
    lines.append("")
    lines.append(_build_alerts_section(pending_alerts, acked_alerts, since_date))

    # Section: Hot-Cadence Deltas
    lines.append("## Hot-Cadence Deltas")
    lines.append("")
    if not hot_deltas:
        lines.append("_No hot-cadence data in window._")
    else:
        lines.append(_build_hot_section(hot_deltas))

    # Section: Warm-Cadence Deltas
    lines.append("## Warm-Cadence Deltas")
    lines.append("")
    if not warm_deltas:
        lines.append("_No warm-cadence data in window._")
        lines.append("")
    else:
        lines.append(_build_cadence_section(warm_deltas, "warm"))

    # Section: Cold-Cadence Deltas
    lines.append("## Cold-Cadence Deltas")
    lines.append("")
    if not cold_deltas:
        lines.append("_No cold-cadence data in window._")
        lines.append("")
    else:
        lines.append(_build_cadence_section(cold_deltas, "cold"))

    # Section: No Significant Deltas
    lines.append("## No Significant Deltas")
    lines.append("")
    lines.append(_build_no_significant_section(clear_deltas))

    content = "\n".join(lines)

    output_path.write_text(content, encoding="utf-8")
    log.info("Delta summary written to %s", output_path)

    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate delta_summary.md for a Signal Dispatch issue"
    )
    parser.add_argument(
        "--issue",
        type=int,
        default=None,
        help="Issue number (default: auto from issues.json next_issue_number)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for delta_summary.md (default: content/research/{issue}/delta_summary.md)",
    )
    args = parser.parse_args()

    out = generate_delta_summary(
        issue_number=args.issue,
        output_path=args.output,
    )
    print(f"Delta summary written to: {out}")


if __name__ == "__main__":
    main()

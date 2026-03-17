"""Delta engine -- compute deltas between prior and current source state.

Five delta types:
  numeric   -- arithmetic diff + % change + historical percentile
  event_set -- cardinality change + category distribution shift
  binary    -- state transition detection with duration
  categorical -- new/removed/reclassified entries
  composite -- cross-field relational changes (DEFERRED -- stub only)

Each compute_* function accepts (prior, current, thresholds) and returns
a standard DeltaResult dict.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Standard output schema
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_delta(
    source: str,
    delta_type: str,
    prior: dict,
    current: dict,
    delta: dict,
    historical_context: dict,
    threshold_status: str,
    threshold_value: Any,
    plain_english: str,
) -> dict:
    """Construct a standard delta result dict."""
    return {
        "source": source,
        "delta_type": delta_type,
        "timestamp": _now_iso(),
        "prior": prior,
        "current": current,
        "delta": delta,
        "historical_context": historical_context,
        "threshold_status": threshold_status,
        "threshold_value": threshold_value,
        "plain_english": plain_english,
    }


# ---------------------------------------------------------------------------
# Threshold evaluation helpers
# ---------------------------------------------------------------------------

def _eval_threshold(value: float, watch: float, notification: float) -> str:
    """Return 'clear', 'watch', or 'breached'."""
    if abs(value) >= abs(notification):
        return "breached"
    if abs(value) >= abs(watch):
        return "watch"
    return "clear"


def _historical_percentile(value: float, history: list[float]) -> int | None:
    """Compute what percentile `value` ranks at within `history`.

    Returns integer 0-100, or None if history is empty.
    """
    if not history:
        return None
    below = sum(1 for h in history if h < value)
    return int(round(100 * below / len(history)))


def _find_last_comparable(
    value: float,
    history: list[dict],
    value_key: str = "value",
    date_key: str = "date",
    tolerance: float = 0.2,
) -> dict | None:
    """Find the most recent historical entry with a similar % change.

    tolerance: fractional tolerance (0.2 = ±20% of value)
    Returns {"date": str, "value": float} or None.
    """
    lo = value * (1 - tolerance)
    hi = value * (1 + tolerance)
    for entry in reversed(history):
        v = entry.get(value_key)
        if v is not None and lo <= v <= hi:
            return {"date": entry.get(date_key, ""), "value": v}
    return None


# ---------------------------------------------------------------------------
# Numeric delta
# ---------------------------------------------------------------------------

def compute_numeric(
    source: str,
    prior_value: float,
    current_value: float,
    prior_as_of: str,
    current_as_of: str,
    field_name: str,
    thresholds: dict,
    history_values: list[float] | None = None,
    history_entries: list[dict] | None = None,
) -> dict:
    """Compute a numeric delta.

    Args:
        source: source name (e.g. "bonbast")
        prior_value: previous measurement
        current_value: current measurement
        prior_as_of: ISO timestamp of prior reading
        current_as_of: ISO timestamp of current reading
        field_name: human label for the field (e.g. "USD/IRR")
        thresholds: sub-dict from thresholds.yaml for this source
        history_values: list of historical values for percentile computation
        history_entries: list of {"date": str, "value": float} for last_comparable

    Returns standard delta dict.
    """
    absolute = current_value - prior_value
    if prior_value != 0:
        percent = (absolute / prior_value) * 100
    else:
        percent = float("inf") if absolute > 0 else float("-inf")

    direction = "adverse" if percent > 0 else ("favorable" if percent < 0 else "flat")

    watch_pct = _extract_pct_threshold(thresholds, "watch")
    notif_pct = _extract_pct_threshold(thresholds, "notification")
    threshold_status = _eval_threshold(percent, watch_pct, notif_pct) if notif_pct else "clear"
    threshold_value = notif_pct

    hist_ctx: dict = {}
    if history_values:
        pct_changes = _compute_pct_changes(history_values)
        hist_ctx["percentile_30d"] = _historical_percentile(abs(percent), pct_changes)
    if history_entries:
        last = _find_last_comparable(percent, history_entries)
        if last:
            hist_ctx["last_comparable"] = last

    plain = _format_numeric_plain(
        source, field_name, prior_value, current_value, percent, hist_ctx
    )

    return _make_delta(
        source=source,
        delta_type="numeric",
        prior={"value": prior_value, "field": field_name, "as_of": prior_as_of},
        current={"value": current_value, "field": field_name, "as_of": current_as_of},
        delta={
            "absolute": round(absolute, 6),
            "percent": round(percent, 2),
            "direction": direction,
        },
        historical_context=hist_ctx,
        threshold_status=threshold_status,
        threshold_value=threshold_value,
        plain_english=plain,
    )


def _extract_pct_threshold(thresholds: dict, level: str) -> float:
    """Pull percent-change threshold value from thresholds config for a level."""
    level_cfg = thresholds.get(level, {})
    for key in (
        "percent_change_48h",
        "vix_percent_change",
        "yield_curve_inversion_change",
        "draw_rate_vs_seasonal",
        "inventory_change_vs_seasonal",
        "sigma_above_30d_mean",
        "price_change_48h",
    ):
        if key in level_cfg:
            val = level_cfg[key]
            # For price_change_48h it's fractional (0.05 = 5%), normalize to pct
            if key == "price_change_48h":
                return float(val) * 100
            return float(val)
    return 0.0


def _compute_pct_changes(values: list[float]) -> list[float]:
    """Compute sequential percent changes from a value list."""
    changes = []
    for i in range(1, len(values)):
        if values[i - 1] != 0:
            changes.append(abs((values[i] - values[i - 1]) / values[i - 1] * 100))
    return changes


def _format_numeric_plain(
    source: str,
    field: str,
    prior: float,
    current: float,
    percent: float,
    hist: dict,
) -> str:
    if percent == 0:
        pct_str = "flat"
    else:
        direction = "+" if percent > 0 else ""
        pct_str = f"{direction}{percent:.1f}%"
    fmt_p = f"{prior:,.0f}" if prior == int(prior) else f"{prior:,.2f}"
    fmt_c = f"{current:,.0f}" if current == int(current) else f"{current:,.2f}"
    base = f"{source.upper()} {field} {fmt_p} -> {fmt_c} ({pct_str})"
    if "percentile_30d" in hist:
        base += f". {hist['percentile_30d']}th percentile of 30d moves"
    if "last_comparable" in hist:
        lc = hist["last_comparable"]
        base += f". Last comparable: {lc.get('date', 'unknown')}"
    return base + "."


# ---------------------------------------------------------------------------
# Event-set delta (GDELT, VIIRS/FIRMS, Oryx, ACLED)
# ---------------------------------------------------------------------------

def compute_event_set(
    source: str,
    prior_count: int,
    current_count: int,
    prior_as_of: str,
    current_as_of: str,
    prior_categories: dict[str, int] | None,
    current_categories: dict[str, int] | None,
    thresholds: dict,
    history_counts: list[float] | None = None,
) -> dict:
    """Compute an event-set delta (cardinality change + category shift).

    Args:
        prior_count / current_count: total article/event counts
        prior_categories / current_categories: {category: count} breakdowns
        history_counts: historical daily counts for sigma computation
    """
    absolute = current_count - prior_count
    percent = (absolute / prior_count * 100) if prior_count else 0.0
    direction = "up" if absolute > 0 else ("down" if absolute < 0 else "flat")

    # Sigma above 30d mean
    sigma_val = None
    if history_counts and len(history_counts) > 1:
        mean = statistics.mean(history_counts)
        stdev = statistics.stdev(history_counts)
        if stdev > 0:
            sigma_val = (current_count - mean) / stdev

    watch_sigma = thresholds.get("watch", {}).get("sigma_above_30d_mean", 1.5)
    notif_sigma = thresholds.get("notification", {}).get("sigma_above_30d_mean", 2.5)

    if sigma_val is not None:
        threshold_status = _eval_threshold(sigma_val, watch_sigma, notif_sigma)
    else:
        threshold_status = "clear"
    threshold_value = notif_sigma

    # Category distribution shift
    cat_shift: dict = {}
    if prior_categories and current_categories:
        all_cats = set(prior_categories) | set(current_categories)
        cat_shift = {
            cat: {
                "prior": prior_categories.get(cat, 0),
                "current": current_categories.get(cat, 0),
                "delta": current_categories.get(cat, 0) - prior_categories.get(cat, 0),
            }
            for cat in all_cats
        }

    hist_ctx: dict = {}
    if sigma_val is not None:
        hist_ctx["sigma_above_30d_mean"] = round(sigma_val, 2)
        if history_counts:
            hist_ctx["30d_mean"] = round(statistics.mean(history_counts), 1)

    sigma_str = f" ({sigma_val:.1f}σ above 30d mean)" if sigma_val is not None else ""
    if absolute == 0:
        count_str = "flat"
    else:
        sign = "+" if absolute > 0 else "-"
        count_str = f"{sign}{abs(percent):.0f}%"
    plain = (
        f"{source.upper()} event count {prior_count} -> {current_count} "
        f"({count_str}){sigma_str}."
    )

    return _make_delta(
        source=source,
        delta_type="event_set",
        prior={"count": prior_count, "categories": prior_categories, "as_of": prior_as_of},
        current={"count": current_count, "categories": current_categories, "as_of": current_as_of},
        delta={
            "absolute": absolute,
            "percent": round(percent, 1),
            "direction": direction,
            "category_shift": cat_shift,
        },
        historical_context=hist_ctx,
        threshold_status=threshold_status,
        threshold_value=threshold_value,
        plain_english=plain,
    )


# ---------------------------------------------------------------------------
# Binary / state delta (OONI, Cloudflare outages)
# ---------------------------------------------------------------------------

def compute_binary(
    source: str,
    prior_state: bool,
    current_state: bool,
    state_label_true: str,
    state_label_false: str,
    prior_as_of: str,
    current_as_of: str,
    state_duration_hours: float | None,
    thresholds: dict,
    new_blocked_endpoints: int | None = None,
) -> dict:
    """Compute a binary/state delta.

    Args:
        prior_state / current_state: boolean state (True = anomaly/blocked)
        state_label_true: human label for True state (e.g. "blocking_active")
        state_label_false: human label for False state (e.g. "normal")
        state_duration_hours: hours since last state change (if known)
        new_blocked_endpoints: count of newly blocked endpoints (for OONI threshold)
    """
    transition = prior_state != current_state
    transition_type = None
    if transition:
        transition_type = "activated" if current_state else "resolved"

    # Threshold logic: new_blocked_endpoints if provided, else state change
    notif_new = thresholds.get("notification", {}).get("new_blocked_endpoints", 2)
    watch_new = thresholds.get("watch", {}).get("new_blocked_endpoints", 1)

    if new_blocked_endpoints is not None:
        threshold_status = _eval_threshold(new_blocked_endpoints, watch_new, notif_new)
        threshold_value = notif_new
    elif transition and current_state:
        threshold_status = "breached"
        threshold_value = 1
    else:
        threshold_status = "clear"
        threshold_value = notif_new

    hist_ctx: dict = {}
    if state_duration_hours is not None:
        hist_ctx["state_duration_hours"] = state_duration_hours

    current_label = state_label_true if current_state else state_label_false
    prior_label = state_label_true if prior_state else state_label_false

    if transition:
        plain = (
            f"{source.upper()} state transition: {prior_label} -> {current_label}."
        )
        if state_duration_hours:
            plain += f" Prior state held {state_duration_hours:.0f}h."
    else:
        plain = f"{source.upper()} state unchanged: {current_label}."
        if new_blocked_endpoints:
            plain += f" {new_blocked_endpoints} new blocked endpoint(s) detected."

    return _make_delta(
        source=source,
        delta_type="binary",
        prior={"state": prior_state, "label": prior_label, "as_of": prior_as_of},
        current={"state": current_state, "label": current_label, "as_of": current_as_of},
        delta={
            "transition": transition,
            "transition_type": transition_type,
            "new_blocked_endpoints": new_blocked_endpoints,
        },
        historical_context=hist_ctx,
        threshold_status=threshold_status,
        threshold_value=threshold_value,
        plain_english=plain,
    )


# ---------------------------------------------------------------------------
# Categorical delta (OFAC, Federal Register, Congress)
# ---------------------------------------------------------------------------

def compute_categorical(
    source: str,
    prior_entries: list[str],
    current_entries: list[str],
    prior_as_of: str,
    current_as_of: str,
    thresholds: dict,
    entry_category: str = "entries",
) -> dict:
    """Compute a categorical delta (new/removed/unchanged sets).

    Args:
        prior_entries / current_entries: lists of entity identifiers
        entry_category: human label for the entry type (e.g. "sanctions entities")
    """
    prior_set = set(prior_entries)
    current_set = set(current_entries)

    added = sorted(current_set - prior_set)
    removed = sorted(prior_set - current_set)
    unchanged_count = len(prior_set & current_set)

    threshold_status = "clear"
    if added or removed:
        threshold_status = "watch"
    if len(added) >= 3 or len(removed) >= 3:
        threshold_status = "breached"
    threshold_value = thresholds.get("notification", {})

    parts = []
    if added:
        parts.append(f"+{len(added)} new {entry_category}")
    if removed:
        parts.append(f"-{len(removed)} removed {entry_category}")
    if not parts:
        parts.append(f"no change ({unchanged_count} {entry_category})")

    plain = f"{source.upper()}: {', '.join(parts)}."
    if added:
        preview = added[:3]
        plain += f" Added: {', '.join(preview)}"
        if len(added) > 3:
            plain += f" (+{len(added) - 3} more)"
        plain += "."

    return _make_delta(
        source=source,
        delta_type="categorical",
        prior={"count": len(prior_entries), "as_of": prior_as_of},
        current={"count": len(current_entries), "as_of": current_as_of},
        delta={
            "added": added,
            "removed": removed,
            "added_count": len(added),
            "removed_count": len(removed),
            "unchanged_count": unchanged_count,
        },
        historical_context={},
        threshold_status=threshold_status,
        threshold_value=threshold_value,
        plain_english=plain,
    )


# ---------------------------------------------------------------------------
# Composite delta -- DEFERRED
# ---------------------------------------------------------------------------

def compute_composite(
    source: str,
    prior: dict,
    current: dict,
    thresholds: dict,
) -> dict:
    """Composite delta -- cross-field relational changes. DEFERRED (Phase 2).

    Stub returns a no-op delta so the daemon can call this without crashing.
    Phase 2 will implement USAspending, Comtrade, FEC cross-field analysis.
    """
    return _make_delta(
        source=source,
        delta_type="composite",
        prior=prior,
        current=current,
        delta={"deferred": True},
        historical_context={},
        threshold_status="clear",
        threshold_value=None,
        plain_english=f"{source.upper()} composite delta deferred to Phase 2.",
    )

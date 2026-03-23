"""
Tests for run_opensanctions — edge cases from the 2026-03-23 bug fix.

Covers:
  1. Normal delta — counts changed across terms
  2. No prior state — baseline recording, returns None
  3. Empty prior snapshot (falsy dict) — treated as no prior
  4. New term appears in current but not prior — baseline 0
  5. Term disappears from current — baseline 0 on current side
  6. All terms unchanged — no signal, returns None
  7. Empty searches — disappeared terms still computed, save proceeds
  8. cross_jurisdiction is tracked as its own numeric field
  9. Primary delta selection — term with highest abs % change wins
 10. poll_opensanctions returns ok=False — early return None, no save
 11. Both prior and current zero for a term — term skipped (no noise)
 12. Prior value 0, current > 0 — inf percent, no crash, sorts as highest signal
"""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

# ---------------------------------------------------------------------------
# Path setup — ensure src/ is importable
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]  # signal-dispatch/
sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PRIOR_AS_OF = "2026-03-22T06:00:00"
CURRENT_AS_OF = "2026-03-23T06:00:00"


def _make_poll_result(searches: dict, cross_jurisdiction: list | None = None, ok: bool = True) -> dict:
    """Build a fake poll_opensanctions response."""
    return {
        "ok": ok,
        "as_of": CURRENT_AS_OF,
        "searches": {
            term: {"total_results": count}
            for term, count in searches.items()
        },
        "cross_jurisdiction": cross_jurisdiction if cross_jurisdiction is not None else [],
        "error": None if ok else "HTTP 401",
    }


def _make_prior(snapshot: dict, as_of: str = PRIOR_AS_OF) -> dict:
    """Build a fake prior state (as stored by _save_prior)."""
    return {"snapshot": snapshot, "as_of": as_of}


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

class TestRunOpensanctions(unittest.IsolatedAsyncioTestCase):

    def _run(self, poll_result: dict, prior_state: dict | None, thresholds: dict | None = None):
        """
        Execute run_opensanctions with mocked I/O.
        Returns (result, saved_calls) where saved_calls is list of dicts passed to _save_prior.
        """
        from src.delta import daemon  # noqa: PLC0415

        saved: list[dict] = []

        def fake_save_prior(source, data):
            saved.append(data)

        with (
            patch.object(daemon, "_load_prior", return_value=prior_state),
            patch.object(daemon, "_save_prior", side_effect=fake_save_prior),
            patch("src.delta.sources.poll_opensanctions", new=AsyncMock(return_value=poll_result)),
        ):
            result = asyncio.get_event_loop().run_until_complete(
                daemon.run_opensanctions(thresholds or {})
            )

        return result, saved

    # ------------------------------------------------------------------
    # 1. Normal delta — counts changed
    # ------------------------------------------------------------------
    def test_normal_delta_returns_primary(self):
        # Iran 100→150 (+50%), Russia unchanged — Iran is primary
        poll = _make_poll_result({"Iran": 150, "Russia": 80}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 100, "Russia": 80, "cross_jurisdiction": 0})
        result, saved = self._run(poll, prior)

        self.assertIsNotNone(result)
        self.assertIn("per_term", result)
        # per_term keys are "opensanctions_<term>"
        self.assertIn("opensanctions_Iran", result["per_term"])
        # Russia and cross_jurisdiction are unchanged — should not appear in per_term
        self.assertNotIn("opensanctions_Russia", result["per_term"])
        # Primary source should be Iran
        self.assertEqual(result["source"], "opensanctions_Iran")

    # ------------------------------------------------------------------
    # 2. No prior state — baseline, returns None
    # ------------------------------------------------------------------
    def test_no_prior_returns_none_and_saves(self):
        poll = _make_poll_result({"Iran": 100})
        result, saved = self._run(poll, prior_state=None)

        self.assertIsNone(result)
        # Should have saved the baseline
        self.assertEqual(len(saved), 1)
        self.assertIn("snapshot", saved[0])
        self.assertEqual(saved[0]["snapshot"]["Iran"], 100)

    # ------------------------------------------------------------------
    # 3. Empty prior snapshot (falsy) — treated as no prior
    # ------------------------------------------------------------------
    def test_empty_prior_snapshot_returns_none(self):
        poll = _make_poll_result({"Iran": 100})
        prior = _make_prior({})  # empty snapshot — falsy
        result, saved = self._run(poll, prior)

        self.assertIsNone(result)
        self.assertEqual(len(saved), 1)  # still saves current as new baseline

    # ------------------------------------------------------------------
    # 4. New term in current, not in prior — uses 0 as baseline
    # ------------------------------------------------------------------
    def test_new_term_uses_zero_baseline(self):
        poll = _make_poll_result({"Iran": 100, "China": 50}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 100, "cross_jurisdiction": 0})  # China not in prior
        result, saved = self._run(poll, prior)

        # China 0→50 should appear; Iran unchanged should not
        self.assertIsNotNone(result)
        per_term = result["per_term"]
        self.assertIn("opensanctions_China", per_term)
        self.assertNotIn("opensanctions_Iran", per_term)
        china_delta = per_term["opensanctions_China"]
        self.assertEqual(china_delta["prior"]["value"], 0.0)
        self.assertEqual(china_delta["current"]["value"], 50.0)

    # ------------------------------------------------------------------
    # 5. Term disappears from current — uses 0 on current side
    # ------------------------------------------------------------------
    def test_disappeared_term_uses_zero_current(self):
        poll = _make_poll_result({"Iran": 100}, cross_jurisdiction=[])  # Russia gone
        prior = _make_prior({"Iran": 100, "Russia": 60, "cross_jurisdiction": 0})
        result, saved = self._run(poll, prior)

        self.assertIsNotNone(result)
        per_term = result["per_term"]
        self.assertIn("opensanctions_Russia", per_term)
        russia_delta = per_term["opensanctions_Russia"]
        self.assertEqual(russia_delta["current"]["value"], 0.0)
        self.assertEqual(russia_delta["prior"]["value"], 60.0)
        # Iran unchanged — not in per_term
        self.assertNotIn("opensanctions_Iran", per_term)

    # ------------------------------------------------------------------
    # 6. All terms unchanged (including cross_jurisdiction) — returns None
    # ------------------------------------------------------------------
    def test_all_terms_unchanged_returns_none(self):
        poll = _make_poll_result({"Iran": 100, "Russia": 60}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 100, "Russia": 60, "cross_jurisdiction": 0})
        result, saved = self._run(poll, prior)

        self.assertIsNone(result)
        self.assertEqual(len(saved), 1)  # still saves snapshot

    # ------------------------------------------------------------------
    # 7. Empty searches — disappeared terms still computed (Iran 100→0)
    # ------------------------------------------------------------------
    def test_empty_searches_computes_disappeared_terms(self):
        poll = _make_poll_result({}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 100, "cross_jurisdiction": 0})

        result, saved = self._run(poll, prior)
        # Iran was in prior, not in current snapshot → treated as 0
        self.assertIsNotNone(result)
        self.assertIn("opensanctions_Iran", result["per_term"])
        iran = result["per_term"]["opensanctions_Iran"]
        self.assertEqual(iran["current"]["value"], 0.0)
        self.assertEqual(iran["prior"]["value"], 100.0)

    # ------------------------------------------------------------------
    # 8. cross_jurisdiction tracked as its own numeric field
    # ------------------------------------------------------------------
    def test_cross_jurisdiction_tracked(self):
        # Iran unchanged, cross_jurisdiction 1→3
        poll = _make_poll_result({"Iran": 100}, cross_jurisdiction=["e1", "e2", "e3"])
        prior = _make_prior({"Iran": 100, "cross_jurisdiction": 1})
        result, saved = self._run(poll, prior)

        self.assertIsNotNone(result)
        per_term = result["per_term"]
        self.assertIn("opensanctions_cross_jurisdiction", per_term)
        cj = per_term["opensanctions_cross_jurisdiction"]
        self.assertEqual(cj["prior"]["value"], 1.0)
        self.assertEqual(cj["current"]["value"], 3.0)
        # Iran unchanged — not in per_term
        self.assertNotIn("opensanctions_Iran", per_term)
        # Primary is cross_jurisdiction (only changed term)
        self.assertEqual(result["source"], "opensanctions_cross_jurisdiction")

    # ------------------------------------------------------------------
    # 9. Primary selection — highest abs % change wins
    # ------------------------------------------------------------------
    def test_primary_is_highest_abs_pct_change(self):
        # Iran: 100→110 (+10%), Russia: 50→25 (-50%) — Russia wins
        poll = _make_poll_result({"Iran": 110, "Russia": 25}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 100, "Russia": 50, "cross_jurisdiction": 0})
        result, saved = self._run(poll, prior)

        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "opensanctions_Russia")

    # ------------------------------------------------------------------
    # 10. poll_opensanctions returns ok=False — early return, no save
    # ------------------------------------------------------------------
    def test_poll_failure_returns_none_no_save(self):
        poll = _make_poll_result({}, ok=False)
        prior = _make_prior({"Iran": 100})
        result, saved = self._run(poll, prior)

        self.assertIsNone(result)
        self.assertEqual(len(saved), 0)  # nothing saved

    # ------------------------------------------------------------------
    # 11. Both prior and current zero — term skipped (no noise)
    # ------------------------------------------------------------------
    def test_both_zero_term_skipped(self):
        # NoData is 0 in both — should be skipped; Iran also unchanged → None
        poll = _make_poll_result({"Iran": 100, "NoData": 0}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 100, "NoData": 0, "cross_jurisdiction": 0})
        result, saved = self._run(poll, prior)

        self.assertIsNone(result)

    def test_both_zero_skipped_but_other_term_has_signal(self):
        poll = _make_poll_result({"Iran": 150, "NoData": 0}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 100, "NoData": 0, "cross_jurisdiction": 0})
        result, saved = self._run(poll, prior)

        self.assertIsNotNone(result)
        per_term = result["per_term"]
        # NoData (both zero) should not appear
        self.assertNotIn("opensanctions_NoData", per_term)
        # Iran (changed) should appear
        self.assertIn("opensanctions_Iran", per_term)

    # ------------------------------------------------------------------
    # 12. Prior value 0, current > 0 — inf percent, no crash, sorts highest
    # ------------------------------------------------------------------
    def test_prior_zero_current_positive_no_crash(self):
        # Iran 0→50 (inf%), Russia 100→90 (-10%) — Iran (inf) should be primary
        poll = _make_poll_result({"Iran": 50, "Russia": 90}, cross_jurisdiction=[])
        prior = _make_prior({"Iran": 0, "Russia": 100, "cross_jurisdiction": 0})
        result, saved = self._run(poll, prior)

        self.assertIsNotNone(result)
        per_term = result["per_term"]
        self.assertIn("opensanctions_Iran", per_term)
        iran_delta = per_term["opensanctions_Iran"]
        self.assertEqual(iran_delta["delta"]["percent"], float("inf"))
        # Iran (inf%) should beat Russia (-10%) as primary
        self.assertEqual(result["source"], "opensanctions_Iran")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)

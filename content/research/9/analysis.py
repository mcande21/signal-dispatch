"""
Signal Dispatch #9 — SAVE Act Analysis
Statistical analysis scripts for quantitative backing of qualitative findings.

Run with: .venv/bin/python content/research/9/analysis.py
Output: content/research/9/data/analysis-results.json
        content/research/9/data/analysis-summary.md
"""

import json
import math
import os
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
RESULTS_FILE = os.path.join(DATA_DIR, "analysis-results.json")
SUMMARY_FILE = os.path.join(DATA_DIR, "analysis-summary.md")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)


def stats(values):
    """Return descriptive stats for a list of floats."""
    if not values:
        return {}
    n = len(values)
    s = sorted(values)
    mean = sum(s) / n
    variance = sum((x - mean) ** 2 for x in s) / n
    std = math.sqrt(variance)
    return {
        "n": n,
        "mean": round(mean, 6),
        "median": round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 6),
        "std": round(std, 6),
        "min": round(s[0], 6),
        "p25": round(s[int(n * 0.25)], 6),
        "p75": round(s[int(n * 0.75)], 6),
        "max": round(s[-1], 6),
    }


# CPS code lookup tables
PES3_LABELS = {
    "1": "Did not meet registration requirements (citizenship/ID)",
    "2": "Did not know where/how to register",
    "3": "Did not meet registration deadline",
    "4": "Not interested/did not want to vote",
    "5": "Permanent illness/disability",
    "6": "Other reason",
    "7": "Don't know",
    "8": "Refused",
    "9": "Not in universe / not reported",
}

# PRCITSHP: 1=Native born US, 2=Native born PR/territory, 3=Native born abroad,
# 4=Naturalized, 5=Non-citizen
PRCITSHP_LABELS = {
    "1": "Native born US",
    "2": "Native born territory",
    "3": "Native born abroad",
    "4": "Naturalized citizen",
    "5": "Non-citizen",
}

# PTDTRACE: simplified groupings for cross-tab
RACE_LABELS = {
    "1": "White only",
    "2": "Black only",
    "3": "American Indian only",
    "4": "Asian only",
    "5": "Hawaiian/PI only",
    "6": "White-Black",
    "7": "White-AI",
    "8": "White-Asian",
    "9": "White-HP",
    "10": "Black-AI",
    "14": "Asian-HP",
    "15": "White-Black-AI",
    "16": "White-AI-Asian",
    "17": "White-Black-Asian",
    "20": "Black-AI-Asian",
    "21": "White-Black-HP",
    "26": "Two or more",
}

# DPOC-amplified barrier codes: codes 1, 2, 3 are directly worsened by
# documentation-of-proof-of-citizenship requirements
DPOC_AMPLIFIED_CODES = {"1", "2", "3"}

# FIPS -> state name mapping (abbreviated)
FIPS_TO_STATE = {
    "1": "Alabama", "2": "Alaska", "4": "Arizona", "5": "Arkansas",
    "6": "California", "8": "Colorado", "9": "Connecticut", "10": "Delaware",
    "11": "DC", "12": "Florida", "13": "Georgia", "15": "Hawaii",
    "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa",
    "20": "Kansas", "21": "Kentucky", "22": "Louisiana", "23": "Maine",
    "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
    "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska",
    "32": "Nevada", "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico",
    "36": "New York", "37": "North Carolina", "38": "North Dakota", "39": "Ohio",
    "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island",
    "45": "South Carolina", "46": "South Dakota", "47": "Tennessee", "48": "Texas",
    "49": "Utah", "50": "Vermont", "51": "Virginia", "53": "Washington",
    "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming",
}

# Target competitive CDs for Analysis 6
TARGET_CDS = {
    "GA-7": "1307",
    "CA-45": "0645",
    "NC-12": "3712",
    "AZ-1":  "0401",
    "WI-3":  "5503",
    "IA-1":  "1901",
}

# Competitive states for Analysis 4
COMPETITIVE_STATES_FIPS = {
    "Georgia":       "13",
    "Michigan":      "26",
    "North Carolina": "37",
    "Arizona":       "4",
    "New Hampshire": "33",
    "Wisconsin":     "55",
    "Iowa":          "19",
    "Nevada":        "32",
    "Pennsylvania":  "42",
}


# ---------------------------------------------------------------------------
# Analysis 1: District Exposure Index
# ---------------------------------------------------------------------------

def analysis_1():
    print("Running Analysis 1: District Exposure Index...")

    cd_cit = load("census-citizenship-by-cd.json")["data"]
    cd_cvap = load("census-cvap-by-cd.json")["data"]

    # Build CVAP lookup by fips
    cvap_by_fips = {r["fips"]: r for r in cd_cvap}

    results = []
    for r in cd_cit:
        total = r["total_18plus"]
        nat = r["naturalized_citizen_18plus"]
        if not total or not nat:
            continue
        nat_share = nat / total
        cvap = cvap_by_fips.get(r["fips"], {}).get("cvap_total", 0)
        results.append({
            "fips": r["fips"],
            "name": r["name"],
            "total_18plus": total,
            "naturalized_citizen_18plus": nat,
            "naturalized_share": round(nat_share, 6),
            "cvap_total": cvap,
        })

    results.sort(key=lambda x: x["naturalized_share"], reverse=True)

    shares = [r["naturalized_share"] for r in results]

    over_10 = [r for r in results if r["naturalized_share"] > 0.10]
    over_15 = [r for r in results if r["naturalized_share"] > 0.15]
    over_20 = [r for r in results if r["naturalized_share"] > 0.20]

    return {
        "top_50": results[:50],
        "bottom_50": results[-50:],
        "distribution": stats(shares),
        "threshold_counts": {
            "over_10pct": len(over_10),
            "over_15pct": len(over_15),
            "over_20pct": len(over_20),
            "total_cds": len(results),
        },
        "over_20pct_districts": [
            {"name": r["name"], "fips": r["fips"],
             "naturalized_share": r["naturalized_share"],
             "naturalized_citizen_18plus": r["naturalized_citizen_18plus"]}
            for r in over_20
        ],
    }


# ---------------------------------------------------------------------------
# Analysis 2: Partisan Impact Model
# ---------------------------------------------------------------------------

def analysis_2():
    print("Running Analysis 2: Partisan Impact Model...")

    # CDCE documentation gap rates (% lacking ready access)
    DEM_RATE = 0.10
    REP_RATE = 0.07
    IND_RATE = 0.13
    SUPPRESSION_RATE = 0.50  # effective suppression (half obtain docs or wouldn't vote)

    CVAP = 500_000

    # Party composition scenarios
    compositions = [
        {"label": "45D/45R/10I", "d": 0.45, "r": 0.45, "i": 0.10},
        {"label": "40D/40R/20I", "d": 0.40, "r": 0.40, "i": 0.20},
        {"label": "48D/47R/5I",  "d": 0.48, "r": 0.47, "i": 0.05},
        {"label": "35D/35R/30I", "d": 0.35, "r": 0.35, "i": 0.30},
        {"label": "50D/42R/8I",  "d": 0.50, "r": 0.42, "i": 0.08},
    ]

    # Independent lean scenarios
    ind_leans = [
        {"label": "50/50 split", "d_frac": 0.50, "r_frac": 0.50},
        {"label": "55D/45R",     "d_frac": 0.55, "r_frac": 0.45},
        {"label": "60D/40R",     "d_frac": 0.60, "r_frac": 0.40},
        {"label": "45D/55R",     "d_frac": 0.45, "r_frac": 0.55},
    ]

    matrix = []
    for comp in compositions:
        for lean in ind_leans:
            d_voters = CVAP * comp["d"]
            r_voters = CVAP * comp["r"]
            i_voters = CVAP * comp["i"]

            # Voters suppressed from each group
            d_suppressed = d_voters * DEM_RATE * SUPPRESSION_RATE
            r_suppressed = r_voters * REP_RATE * SUPPRESSION_RATE
            i_suppressed = i_voters * IND_RATE * SUPPRESSION_RATE

            # Independent suppressed votes split by lean
            i_d_suppressed = i_suppressed * lean["d_frac"]
            i_r_suppressed = i_suppressed * lean["r_frac"]

            net_d_loss = d_suppressed + i_d_suppressed
            net_r_loss = r_suppressed + i_r_suppressed
            net_d_advantage_loss = net_d_loss - net_r_loss  # positive = D loses more

            matrix.append({
                "composition": comp["label"],
                "ind_lean": lean["label"],
                "d_voters": round(d_voters),
                "r_voters": round(r_voters),
                "i_voters": round(i_voters),
                "d_suppressed": round(d_suppressed),
                "r_suppressed": round(r_suppressed),
                "i_suppressed": round(i_suppressed),
                "net_d_loss": round(net_d_loss),
                "net_r_loss": round(net_r_loss),
                "net_d_r_differential": round(net_d_advantage_loss),
                "d_net_votes_lost": round(net_d_loss - net_r_loss),
            })

    return {
        "assumptions": {
            "cdce_dem_gap_rate": DEM_RATE,
            "cdce_rep_gap_rate": REP_RATE,
            "cdce_ind_gap_rate": IND_RATE,
            "effective_suppression_rate": SUPPRESSION_RATE,
            "modeled_cvap": CVAP,
        },
        "matrix": matrix,
        "summary": {
            "min_net_d_loss": min(m["net_d_r_differential"] for m in matrix),
            "max_net_d_loss": max(m["net_d_r_differential"] for m in matrix),
            "mean_net_d_loss": round(sum(m["net_d_r_differential"] for m in matrix) / len(matrix)),
        },
    }


# ---------------------------------------------------------------------------
# Analysis 3: CPS Barrier Analysis
# ---------------------------------------------------------------------------

def analysis_3():
    print("Running Analysis 3: CPS Barrier Analysis...")

    d = load("cps-registration-barriers-2024.json")
    records = d["records"]

    # Weighted barrier frequency
    weighted_by_pes3 = defaultdict(float)
    unweighted_by_pes3 = defaultdict(int)
    for r in records:
        code = r["PES3"]
        weight = float(r["PWSSWGT"])
        weighted_by_pes3[code] += weight
        unweighted_by_pes3[code] += 1

    total_weighted = sum(weighted_by_pes3.values())
    barrier_freq = []
    for code in sorted(weighted_by_pes3.keys()):
        w = weighted_by_pes3[code]
        barrier_freq.append({
            "pes3_code": code,
            "label": PES3_LABELS.get(code, "Unknown"),
            "unweighted_count": unweighted_by_pes3[code],
            "weighted_count": round(w),
            "weighted_pct": round(w / total_weighted * 100, 2),
            "dpoc_amplified": code in DPOC_AMPLIFIED_CODES,
        })

    # Cross-tab: barrier × citizenship
    cross_cit = defaultdict(lambda: defaultdict(float))
    for r in records:
        cross_cit[r["PES3"]][r["PRCITSHP"]] += float(r["PWSSWGT"])

    citizenship_crosstab = {}
    for pes3, cit_dict in cross_cit.items():
        row_total = sum(cit_dict.values())
        citizenship_crosstab[pes3] = {
            "label": PES3_LABELS.get(pes3, "Unknown"),
            "by_citizenship": {
                cit: {
                    "weighted_count": round(wt),
                    "pct_of_barrier": round(wt / row_total * 100, 2),
                    "citizenship_label": PRCITSHP_LABELS.get(cit, "Unknown"),
                }
                for cit, wt in cit_dict.items()
            },
        }

    # Cross-tab: barrier × race (simplified to White/Black/Asian/Other)
    def simplify_race(code):
        if code == "1":
            return "White"
        elif code == "2":
            return "Black"
        elif code == "4":
            return "Asian"
        else:
            return "Other"

    cross_race = defaultdict(lambda: defaultdict(float))
    for r in records:
        cross_race[r["PES3"]][simplify_race(r["PTDTRACE"])] += float(r["PWSSWGT"])

    race_crosstab = {}
    for pes3, race_dict in cross_race.items():
        row_total = sum(race_dict.values())
        race_crosstab[pes3] = {
            "label": PES3_LABELS.get(pes3, "Unknown"),
            "by_race": {
                race: {
                    "weighted_count": round(wt),
                    "pct_of_barrier": round(wt / row_total * 100, 2),
                }
                for race, wt in sorted(race_dict.items())
            },
        }

    # DPOC-amplified summary
    dpoc_codes = DPOC_AMPLIFIED_CODES
    dpoc_weighted = sum(weighted_by_pes3[c] for c in dpoc_codes if c in weighted_by_pes3)
    dpoc_pct = dpoc_weighted / total_weighted * 100

    # Naturalized citizen barrier breakdown
    nat_barriers = defaultdict(float)
    for r in records:
        if r["PRCITSHP"] == "4":  # Naturalized
            nat_barriers[r["PES3"]] += float(r["PWSSWGT"])
    nat_total = sum(nat_barriers.values())
    nat_dpoc = sum(nat_barriers[c] for c in dpoc_codes if c in nat_barriers)

    return {
        "barrier_frequency": barrier_freq,
        "citizenship_crosstab": citizenship_crosstab,
        "race_crosstab": race_crosstab,
        "dpoc_amplified_summary": {
            "dpoc_amplified_codes": sorted(list(dpoc_codes)),
            "dpoc_amplified_pct_of_all_non_registrants": round(dpoc_pct, 2),
            "dpoc_weighted_count": round(dpoc_weighted),
            "naturalized_citizen_barriers": {
                "total_weighted": round(nat_total),
                "dpoc_amplified_weighted": round(nat_dpoc),
                "dpoc_amplified_pct": round(nat_dpoc / nat_total * 100, 2) if nat_total > 0 else 0,
            },
        },
    }


# ---------------------------------------------------------------------------
# Analysis 4: CPS Turnout Gap Analysis
# ---------------------------------------------------------------------------

def analysis_4():
    print("Running Analysis 4: CPS Turnout Gap Analysis...")

    d = load("cps-citizenship-turnout-2024.json")
    national = d["national_summary"]
    by_state = d["by_state"]

    native_national = national["native_born"]["turnout_rate_unweighted"]
    nat_national = national["naturalized"]["turnout_rate_unweighted"]
    national_gap = native_national - nat_national

    # State-level gaps
    state_gaps = []
    for fips_str, state_data in by_state.items():
        native = state_data.get("native_born", {})
        naturalized = state_data.get("naturalized", {})

        native_rate = native.get("turnout_rate_unweighted", 0)
        nat_rate = naturalized.get("turnout_rate_unweighted", 0)
        nat_count = naturalized.get("record_count", 0)

        # Only include if we have meaningful sample sizes (>=10 naturalized records)
        if nat_count < 10:
            continue

        gap = native_rate - nat_rate
        state_name = FIPS_TO_STATE.get(fips_str.lstrip("0"), f"FIPS {fips_str}")

        state_gaps.append({
            "fips": fips_str,
            "state": state_name,
            "native_turnout": round(native_rate, 4),
            "naturalized_turnout": round(nat_rate, 4),
            "gap": round(gap, 4),
            "naturalized_record_count": nat_count,
        })

    state_gaps.sort(key=lambda x: x["gap"], reverse=True)

    # Load census state data for voter count estimates
    state_cit = load("census-citizenship-by-state.json")["data"]
    nat_by_state_name = {r["name"]: r["naturalized_citizen_18plus"] for r in state_cit}

    # Competitive state analysis
    ADDITIONAL_DPOC_DROP = 0.02  # 2pp additional suppression from DPOC requirements
    competitive_analysis = []

    for state_name, fips in COMPETITIVE_STATES_FIPS.items():
        # Find in state_gaps
        state_entry = next((s for s in state_gaps if s["state"] == state_name), None)

        nat_pop = nat_by_state_name.get(state_name, 0)
        # Turnout rate from CPS
        nat_rate = None
        if state_entry:
            nat_rate = state_entry["naturalized_turnout"]
        else:
            nat_rate = nat_national  # fallback to national

        # Current naturalized voters
        current_voters = nat_pop * nat_rate
        # Voters lost from 2pp additional drop
        voters_lost = nat_pop * ADDITIONAL_DPOC_DROP
        # As pct of current naturalized voters
        pct_impact = voters_lost / current_voters * 100 if current_voters > 0 else 0

        competitive_analysis.append({
            "state": state_name,
            "naturalized_pop_18plus": nat_pop,
            "current_naturalized_turnout": round(nat_rate, 4) if nat_rate else None,
            "current_naturalized_voters_est": round(current_voters),
            "voters_lost_at_2pp_drop": round(voters_lost),
            "pct_of_naturalized_vote_lost": round(pct_impact, 2),
            "gap_vs_native": state_entry["gap"] if state_entry else None,
            "sample_size_flag": "small_sample" if not state_entry else "ok",
        })

    competitive_analysis.sort(key=lambda x: x["voters_lost_at_2pp_drop"], reverse=True)

    return {
        "national": {
            "native_born_turnout": round(native_national, 4),
            "naturalized_turnout": round(nat_national, 4),
            "gap": round(national_gap, 4),
            "note": "Unweighted rates from CPS 2024 microdata",
        },
        "state_gaps_ranked": state_gaps,
        "competitive_state_impact": competitive_analysis,
        "methodology_note": (
            "2pp additional suppression scenario is conservative estimate. "
            "Actual effect depends on DPOC implementation, DMV integration, "
            "and naturalized citizen compliance/awareness rates."
        ),
    }


# ---------------------------------------------------------------------------
# Analysis 5: Historical Before/After (Arizona)
# ---------------------------------------------------------------------------

def analysis_5():
    print("Running Analysis 5: Historical Before/After (Arizona)...")

    d = load("elections-az-house.json")
    az_data = d["data"].get("AZ", {})

    # NOTE on data structure: top_candidates contains only the top 5 candidates
    # by vote total per year statewide. In 2000/2002, no Democrat cracked the
    # top 5 statewide — this is a reflection of AZ's R-dominant delegation before
    # Prop 200, not a data error. Per-year stats are computed where data exists.

    def party_votes(year_data):
        d_votes = 0
        r_votes = 0
        i_votes = 0
        d_candidates = 0
        r_candidates = 0
        for c in year_data.get("top_candidates", []):
            if c["party"] == "democrat":
                d_votes += c["votes"]
                d_candidates += 1
            elif c["party"] == "republican":
                r_votes += c["votes"]
                r_candidates += 1
            else:
                i_votes += c["votes"]
        return d_votes, r_votes, i_votes, d_candidates, r_candidates

    before_years = ["2000", "2002"]
    after_years = ["2004", "2006", "2008"]

    year_breakdown = {}

    for yr in before_years + after_years:
        if yr in az_data:
            dv, rv, iv, dc, rc = party_votes(az_data[yr])
            total = az_data[yr]["total_votes"]
            year_breakdown[yr] = {
                "total_votes": total,
                "d_votes": dv,
                "r_votes": rv,
                "other_votes": iv,
                "d_candidates_in_top5": dc,
                "r_candidates_in_top5": rc,
                # Per-candidate averages where applicable
                "avg_d_vote_share": (
                    round(sum(c["vote_share"] for c in az_data[yr]["top_candidates"]
                              if c["party"] == "democrat") / dc, 4)
                    if dc > 0 else None
                ),
                "avg_r_vote_share": (
                    round(sum(c["vote_share"] for c in az_data[yr]["top_candidates"]
                              if c["party"] == "republican") / rc, 4)
                    if rc > 0 else None
                ),
                "period": "before" if yr in before_years else "after",
            }

    # Prop 200 context: use avg R candidate vote share as a proxy for
    # partisan environment (D candidate absence in top 5 in 2000/2002
    # reflects pre-competitive delegation, not an artifact)
    before_avg_r = [
        year_breakdown[yr]["avg_r_vote_share"]
        for yr in before_years
        if year_breakdown.get(yr, {}).get("avg_r_vote_share")
    ]
    after_avg_r = [
        year_breakdown[yr]["avg_r_vote_share"]
        for yr in after_years
        if year_breakdown.get(yr, {}).get("avg_r_vote_share")
    ]
    before_avg_d = [
        year_breakdown[yr]["avg_d_vote_share"]
        for yr in before_years
        if year_breakdown.get(yr, {}).get("avg_d_vote_share")
    ]
    after_avg_d = [
        year_breakdown[yr]["avg_d_vote_share"]
        for yr in after_years
        if year_breakdown.get(yr, {}).get("avg_d_vote_share")
    ]

    mean_before_r = sum(before_avg_r) / len(before_avg_r) if before_avg_r else None
    mean_after_r = sum(after_avg_r) / len(after_avg_r) if after_avg_r else None
    mean_before_d = sum(before_avg_d) / len(before_avg_d) if before_avg_d else None
    mean_after_d = sum(after_avg_d) / len(after_avg_d) if after_avg_d else None

    total_votes_before = sum(az_data[yr]["total_votes"] for yr in before_years if yr in az_data)
    total_votes_after = sum(az_data[yr]["total_votes"] for yr in after_years if yr in az_data)

    return {
        "policy_boundary": "Arizona Proposition 200 (2004 implementation)",
        "data_caveat": (
            "Dataset contains top-5 candidates per election cycle only. "
            "In 2000/2002 no Democrat ranked in the top 5 statewide — AZ had "
            "an all-Republican delegation. D candidates appear in 2006/2008 "
            "as competitive seats emerged. "
            "This is NOT causal. Confounds: national wave (2006, 2008 D wave), "
            "candidate recruitment, AZ population growth. Treat as context only."
        ),
        "total_votes": {
            "before_sum": total_votes_before,
            "after_sum": total_votes_after,
            "change_pct": round((total_votes_after - total_votes_before) / total_votes_before * 100, 1) if total_votes_before else None,
        },
        "avg_r_candidate_vote_share": {
            "before": round(mean_before_r * 100, 2) if mean_before_r else None,
            "after": round(mean_after_r * 100, 2) if mean_after_r else None,
            "change_ppt": round((mean_after_r - mean_before_r) * 100, 2) if (mean_before_r and mean_after_r) else None,
        },
        "avg_d_candidate_vote_share": {
            "before": None,
            "after": round(mean_after_d * 100, 2) if mean_after_d else None,
            "note": "D candidates absent from top-5 in before period (2000, 2002)",
        },
        "d_candidates_emerging": {
            "2006": year_breakdown.get("2006", {}).get("d_candidates_in_top5", 0),
            "2008": year_breakdown.get("2008", {}).get("d_candidates_in_top5", 0),
            "interpretation": (
                "D candidates began appearing in competitive positions after Prop 200. "
                "Causal attribution impossible without controls for national environment."
            ),
        },
        "year_breakdown": year_breakdown,
    }


# ---------------------------------------------------------------------------
# Analysis 6: Race-Specific CD Exposure
# ---------------------------------------------------------------------------

def analysis_6():
    print("Running Analysis 6: Race-Specific CD Exposure...")

    cd_total = {r["fips"]: r for r in load("census-citizenship-by-cd.json")["data"]}
    cd_hisp = {r["fips"]: r for r in load("census-citizenship-hispanic-by-cd.json")["data"]}
    cd_black = {r["fips"]: r for r in load("census-citizenship-black-by-cd.json")["data"]}

    # CDCE documentation gap rates
    CDCE_OVERALL = 0.09  # ~9% overall (midpoint of 7-13 range)

    results = {}
    for label, fips in TARGET_CDS.items():
        total_r = cd_total.get(fips, {})
        hisp_r = cd_hisp.get(fips, {})
        black_r = cd_black.get(fips, {})

        if not total_r:
            results[label] = {"error": f"No data for FIPS {fips}"}
            continue

        total_18plus = total_r.get("total_18plus", 0)
        nat_total = total_r.get("naturalized_citizen_18plus", 0)
        nat_share = nat_total / total_18plus if total_18plus else 0

        nat_hisp = hisp_r.get("naturalized_citizen_18plus", 0)
        hisp_total = hisp_r.get("total_18plus", 0)
        nat_hisp_share = nat_hisp / total_18plus if total_18plus else 0  # as share of all 18+

        nat_black = black_r.get("naturalized_citizen_18plus", 0)
        black_total = black_r.get("total_18plus", 0)
        nat_black_share = nat_black / total_18plus if total_18plus else 0

        # Affected voters estimate: naturalized * CDCE_OVERALL * 0.5 effective suppression
        est_affected = round(nat_total * CDCE_OVERALL * 0.5)
        hisp_affected = round(nat_hisp * CDCE_OVERALL * 0.5)
        black_affected = round(nat_black * CDCE_OVERALL * 0.5)

        results[label] = {
            "fips": fips,
            "name": total_r.get("name", ""),
            "total_18plus": total_18plus,
            "naturalized_total": nat_total,
            "naturalized_share_pct": round(nat_share * 100, 2),
            "naturalized_hispanic": nat_hisp,
            "naturalized_hispanic_share_of_18plus_pct": round(nat_hisp_share * 100, 2),
            "naturalized_black": nat_black,
            "naturalized_black_share_of_18plus_pct": round(nat_black_share * 100, 2),
            "estimated_affected_voters": {
                "all_naturalized": est_affected,
                "hispanic_naturalized": hisp_affected,
                "black_naturalized": black_affected,
                "methodology": (
                    "naturalized_pop * 9% CDCE gap rate * 50% effective suppression"
                ),
            },
        }

    return {
        "methodology_note": (
            "FIPS codes: first 2 digits = state, last 2 = CD number. "
            "Hispanic/Black naturalized counts are subsets (may overlap). "
            "Affected voters = naturalized pop * CDCE_OVERALL (9%) * 50% effective suppression. "
            "50% suppression assumes half will obtain docs or would not have voted."
        ),
        "districts": results,
    }


# ---------------------------------------------------------------------------
# Analysis 7: Education-Poverty Intersection
# ---------------------------------------------------------------------------

def analysis_7():
    print("Running Analysis 7: Education-Poverty Intersection...")

    edu_data = load("census-nativity-education.json")["data"]
    pov_data = load("census-nativity-poverty.json")["data"]

    pov_by_name = {r["name"]: r for r in pov_data}

    state_profiles = []
    for r in edu_data:
        state = r["name"]
        pov_r = pov_by_name.get(state, {})

        foreign_total_edu = r.get("foreign_total", 0)
        foreign_less_hs = r.get("foreign_less_than_hs", 0)
        less_hs_pct = foreign_less_hs / foreign_total_edu * 100 if foreign_total_edu else 0

        foreign_total_pov = pov_r.get("foreign_total", 0)
        foreign_poverty = pov_r.get("foreign_below_100pct", 0)
        poverty_pct = foreign_poverty / foreign_total_pov * 100 if foreign_total_pov else 0

        # Intersection proxy: assume independence (not strictly valid but directionally useful)
        # P(low_edu AND poverty) ≈ P(low_edu) * P(poverty) as lower bound
        # Real intersection is higher due to correlation
        intersection_lower_bound_pct = (less_hs_pct / 100) * (poverty_pct / 100) * 100
        # Weighted intersection estimate: use 1.5x correlation adjustment
        intersection_est_pct = intersection_lower_bound_pct * 1.5

        state_profiles.append({
            "state": state,
            "fips": r["fips"],
            "foreign_total": foreign_total_edu,
            "foreign_less_than_hs": foreign_less_hs,
            "foreign_less_than_hs_pct": round(less_hs_pct, 2),
            "foreign_below_poverty": foreign_poverty,
            "foreign_poverty_pct": round(poverty_pct, 2),
            "intersection_lower_bound_pct": round(intersection_lower_bound_pct, 2),
            "intersection_est_pct": round(intersection_est_pct, 2),
            "documentation_barrier_risk": (
                "HIGH" if less_hs_pct > 30 and poverty_pct > 15 else
                "MODERATE" if less_hs_pct > 20 or poverty_pct > 12 else
                "LOWER"
            ),
        })

    state_profiles.sort(key=lambda x: x["intersection_est_pct"], reverse=True)

    # Distribution stats
    hs_pcts = [s["foreign_less_than_hs_pct"] for s in state_profiles if s["foreign_less_than_hs_pct"] > 0]
    pov_pcts = [s["foreign_poverty_pct"] for s in state_profiles if s["foreign_poverty_pct"] > 0]

    high_risk = [s for s in state_profiles if s["documentation_barrier_risk"] == "HIGH"]
    moderate_risk = [s for s in state_profiles if s["documentation_barrier_risk"] == "MODERATE"]

    return {
        "state_profiles": state_profiles,
        "distribution": {
            "less_than_hs_education": stats(hs_pcts),
            "below_poverty": stats(pov_pcts),
        },
        "risk_summary": {
            "high_risk_states": len(high_risk),
            "moderate_risk_states": len(moderate_risk),
            "high_risk_state_names": [s["state"] for s in high_risk],
        },
        "methodology_note": (
            "Intersection estimate uses independence assumption * 1.5 correlation adjustment. "
            "True intersection is likely higher — education and poverty are positively correlated. "
            "HIGH risk = >30% less-than-HS AND >15% poverty. "
            "MODERATE risk = >20% less-than-HS OR >12% poverty."
        ),
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main():
    print("=== Signal Dispatch #9: SAVE Act Analysis ===\n")

    results = {}
    results["analysis_1_district_exposure"] = analysis_1()
    results["analysis_2_partisan_impact"] = analysis_2()
    results["analysis_3_barrier_analysis"] = analysis_3()
    results["analysis_4_turnout_gap"] = analysis_4()
    results["analysis_5_az_before_after"] = analysis_5()
    results["analysis_6_race_cd_exposure"] = analysis_6()
    results["analysis_7_education_poverty"] = analysis_7()

    print(f"\nWriting results to {RESULTS_FILE}...")
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
    print("Done.")

    # Build human-readable summary
    write_summary(results)
    print(f"Summary written to {SUMMARY_FILE}")


def write_summary(r):
    a1 = r["analysis_1_district_exposure"]
    a2 = r["analysis_2_partisan_impact"]
    a3 = r["analysis_3_barrier_analysis"]
    a4 = r["analysis_4_turnout_gap"]
    a5 = r["analysis_5_az_before_after"]
    a6 = r["analysis_6_race_cd_exposure"]
    a7 = r["analysis_7_education_poverty"]

    lines = []
    lines.append("# Signal Dispatch #9 — SAVE Act Analysis Summary")
    lines.append("")
    lines.append("Statistical analysis supporting the SAVE Act deep dive.")
    lines.append("All figures derived from Census ACS, CPS 2024 microdata, and CDCE documentation.")
    lines.append("")

    # A1
    lines.append("## Analysis 1: District Exposure Index")
    lines.append("")
    tc = a1["threshold_counts"]
    dist = a1["distribution"]
    lines.append(f"- **Total CDs analyzed:** {tc['total_cds']}")
    lines.append(f"- **CDs with >10% naturalized share:** {tc['over_10pct']} ({round(tc['over_10pct']/tc['total_cds']*100,1)}%)")
    lines.append(f"- **CDs with >15% naturalized share:** {tc['over_15pct']} ({round(tc['over_15pct']/tc['total_cds']*100,1)}%)")
    lines.append(f"- **CDs with >20% naturalized share:** {tc['over_20pct']} ({round(tc['over_20pct']/tc['total_cds']*100,1)}%)")
    lines.append(f"- **National mean naturalized share:** {round(dist['mean']*100,1)}%")
    lines.append(f"- **National median naturalized share:** {round(dist['median']*100,1)}%")
    lines.append(f"- **Std deviation:** {round(dist['std']*100,1)}pp")
    lines.append("")
    lines.append("**Top 10 CDs by naturalized share:**")
    lines.append("")
    lines.append("| Rank | District | Naturalized Share | Naturalized Pop |")
    lines.append("|------|----------|-------------------|-----------------|")
    for i, cd in enumerate(a1["top_50"][:10], 1):
        lines.append(f"| {i} | {cd['name']} | {round(cd['naturalized_share']*100,1)}% | {cd['naturalized_citizen_18plus']:,} |")
    lines.append("")
    if a1["over_20pct_districts"]:
        lines.append(f"**{len(a1['over_20pct_districts'])} districts exceed 20% naturalized share** — these face the highest SAVE Act exposure.")
    lines.append("")

    # A2
    lines.append("## Analysis 2: Partisan Impact Model")
    lines.append("")
    assum = a2["assumptions"]
    lines.append(f"Modeled CVAP: {assum['modeled_cvap']:,} (typical competitive CD)")
    lines.append(f"CDCE gap rates: D={assum['cdce_dem_gap_rate']*100:.0f}%, R={assum['cdce_rep_gap_rate']*100:.0f}%, I={assum['cdce_ind_gap_rate']*100:.0f}%")
    lines.append(f"Effective suppression assumed: {assum['effective_suppression_rate']*100:.0f}%")
    lines.append("")
    lines.append("**Net D-R voter differential (positive = Democrats lose more):**")
    lines.append("")
    lines.append("| Party Composition | Ind Lean | D Suppressed | R Suppressed | Net D Loss |")
    lines.append("|-------------------|----------|-------------|-------------|------------|")
    for m in a2["matrix"]:
        lines.append(f"| {m['composition']} | {m['ind_lean']} | {m['net_d_loss']:,} | {m['net_r_loss']:,} | **{m['net_d_r_differential']:+,}** |")
    lines.append("")
    summary = a2["summary"]
    lines.append(f"- **Range of net D disadvantage:** {summary['min_net_d_loss']:+,} to {summary['max_net_d_loss']:+,} votes")
    lines.append(f"- **Mean net D disadvantage:** {summary['mean_net_d_loss']:+,} votes per competitive CD")
    lines.append("")

    # A3
    lines.append("## Analysis 3: CPS Barrier Analysis")
    lines.append("")
    lines.append("**Registration barrier frequency (weighted):**")
    lines.append("")
    lines.append("| Barrier | Label | Weighted Pop | Share | DPOC-Amplified |")
    lines.append("|---------|-------|-------------|-------|----------------|")
    for b in a3["barrier_frequency"]:
        dpoc_flag = "YES" if b["dpoc_amplified"] else ""
        lines.append(f"| PES3={b['pes3_code']} | {b['label'][:50]} | {b['weighted_count']:,} | {b['weighted_pct']}% | {dpoc_flag} |")
    lines.append("")
    dpoc_sum = a3["dpoc_amplified_summary"]
    lines.append(f"**DPOC-amplified barriers represent {dpoc_sum['dpoc_amplified_pct_of_all_non_registrants']}% of all non-registrant barriers** (~{dpoc_sum['dpoc_weighted_count']:,} people).")
    nat_b = dpoc_sum["naturalized_citizen_barriers"]
    lines.append(f"Among naturalized citizens specifically: {nat_b['dpoc_amplified_pct']}% of their barriers are DPOC-amplified ({nat_b['dpoc_amplified_weighted']:,} weighted).")
    lines.append("")

    # A4
    lines.append("## Analysis 4: CPS Turnout Gap Analysis")
    lines.append("")
    nat4 = a4["national"]
    lines.append(f"- **National native-born turnout (2024):** {nat4['native_born_turnout']*100:.1f}%")
    lines.append(f"- **National naturalized citizen turnout (2024):** {nat4['naturalized_turnout']*100:.1f}%")
    lines.append(f"- **Existing gap:** {nat4['gap']*100:.1f}pp ({nat4['note']})")
    lines.append("")
    lines.append("**Competitive state impact (2pp additional DPOC suppression scenario):**")
    lines.append("")
    lines.append("| State | Naturalized Pop | Current Turnout | Voters Lost (2pp) |")
    lines.append("|-------|-----------------|-----------------|-------------------|")
    for s in a4["competitive_state_impact"]:
        flag = " *" if s["sample_size_flag"] == "small_sample" else ""
        lines.append(f"| {s['state']}{flag} | {s['naturalized_pop_18plus']:,} | {(s['current_naturalized_turnout'] or 0)*100:.1f}% | **{s['voters_lost_at_2pp_drop']:,}** |")
    lines.append("")
    lines.append("\\* Small sample size — using national rate as fallback.")
    lines.append("")

    # A5
    lines.append("## Analysis 5: Arizona Before/After (Prop 200)")
    lines.append("")
    lines.append(f"**Policy boundary:** {a5['policy_boundary']}")
    lines.append("")
    tv = a5["total_votes"]
    lines.append(f"- **Total AZ House votes (2000, 2002):** {tv['before_sum']:,}")
    lines.append(f"- **Total AZ House votes (2004-2008):** {tv['after_sum']:,}")
    lines.append(f"- **Vote total growth:** {tv['change_pct']:+.1f}%")
    lines.append("")
    r_share = a5["avg_r_candidate_vote_share"]
    d_share = a5["avg_d_candidate_vote_share"]
    lines.append(f"- **Avg R candidate vote share before:** {r_share['before']}%")
    lines.append(f"- **Avg R candidate vote share after:** {r_share['after']}% ({r_share['change_ppt']:+.1f}pp)")
    lines.append(f"- **D candidates in top 5 after:** 2006={a5['d_candidates_emerging']['2006']}, 2008={a5['d_candidates_emerging']['2008']}")
    lines.append(f"- **D candidate avg vote share after:** {d_share['after']}%")
    lines.append("")
    lines.append(f"> **Data caveat:** {a5['data_caveat']}")
    lines.append("")

    # A6
    lines.append("## Analysis 6: Race-Specific CD Exposure (Target Districts)")
    lines.append("")
    lines.append("| District | Nat. Share | Nat. Hispanic Share | Nat. Black Share | Est. Affected |")
    lines.append("|----------|-----------|---------------------|-----------------|---------------|")
    for label, cd in a6["districts"].items():
        if "error" in cd:
            lines.append(f"| {label} | ERROR | — | — | — |")
        else:
            lines.append(
                f"| {label} ({cd['fips']}) "
                f"| {cd['naturalized_share_pct']}% "
                f"| {cd['naturalized_hispanic_share_of_18plus_pct']}% "
                f"| {cd['naturalized_black_share_of_18plus_pct']}% "
                f"| {cd['estimated_affected_voters']['all_naturalized']:,} |"
            )
    lines.append("")
    lines.append(f"> *Methodology: {a6['methodology_note']}*")
    lines.append("")

    # A7
    lines.append("## Analysis 7: Education-Poverty Intersection")
    lines.append("")
    risk = a7["risk_summary"]
    lines.append(f"- **High documentation-barrier-risk states:** {risk['high_risk_states']}")
    lines.append(f"  - {', '.join(risk['high_risk_state_names'])}")
    lines.append(f"- **Moderate risk states:** {risk['moderate_risk_states']}")
    lines.append("")
    edu_stats = a7["distribution"]["less_than_hs_education"]
    pov_stats = a7["distribution"]["below_poverty"]
    lines.append(f"- **Foreign-born less-than-HS education (national mean):** {edu_stats['mean']}%")
    lines.append(f"- **Foreign-born below poverty (national mean):** {pov_stats['mean']}%")
    lines.append("")
    lines.append("**Top 15 states by estimated documentation barrier intersection:**")
    lines.append("")
    lines.append("| Rank | State | <HS Edu % | Poverty % | Intersection Est | Risk |")
    lines.append("|------|-------|-----------|-----------|-----------------|------|")
    for i, s in enumerate(a7["state_profiles"][:15], 1):
        lines.append(
            f"| {i} | {s['state']} "
            f"| {s['foreign_less_than_hs_pct']}% "
            f"| {s['foreign_poverty_pct']}% "
            f"| {s['intersection_est_pct']}% "
            f"| {s['documentation_barrier_risk']} |"
        )
    lines.append("")
    lines.append(f"> *{a7['methodology_note']}*")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by Signal Dispatch #9 analysis.py*")

    with open(SUMMARY_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

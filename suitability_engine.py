"""
suitability_engine.py
----------------------
Implements the hybrid decision framework recommended in the project brief
(section 13): HARD EXCLUSION RULES + WEIGHTED MULTI-CRITERIA SUITABILITY.

    SI = wH*H + wD*D + wF*F + wS*S + wE*E + wC*C + wSub*Sub

Every criterion function below maps a raw WP2/WP3 indicator onto a 0-100
"suitability" scale using literature-informed but ADJUSTABLE membership
ranges (see the IDEAL_RANGES dict). Nothing here is a black box: every
score keeps its per-criterion contribution so the DST can show its work
(section 12), and every classification records which hard rule (if any)
fired, and which criterion is the primary constraint.

Swap in real ecological thresholds for the KLCRS as WP1-WP3 evidence
accumulates -- this module is the single place that encodes them.
"""

from dataclasses import replace
from typing import Dict, List, Tuple

from data_model import (
    Site, Classification, ConfidenceLevel, ResilienceCategory, SCENARIOS,
)

# ---------------------------------------------------------------------------
# 1. Criterion weights (must sum to 1.0)
# ---------------------------------------------------------------------------

WEIGHTS = {
    "hydroperiod": 0.20,
    "depth": 0.17,
    "frequency": 0.15,
    "salinity": 0.15,
    "elevation": 0.13,
    "connectivity": 0.12,
    "substrate": 0.08,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

CRITERION_LABELS = {
    "hydroperiod": "Hydroperiod",
    "depth": "Inundation depth",
    "frequency": "Inundation frequency",
    "salinity": "Salinity",
    "elevation": "Elevation",
    "connectivity": "Freshwater connectivity",
    "substrate": "Substrate",
}

# ---------------------------------------------------------------------------
# 2. Membership functions: raw indicator -> 0-100 suitability
#    Trapezoidal shape: (hard_low, ideal_low, ideal_high, hard_high)
#    Below hard_low or above hard_high -> 0. Between ideal_low/high -> 100.
#    Linear ramps in between.
# ---------------------------------------------------------------------------

def _trapezoid(x: float, hard_low: float, ideal_low: float, ideal_high: float, hard_high: float) -> float:
    if x <= hard_low or x >= hard_high:
        return 0.0
    if ideal_low <= x <= ideal_high:
        return 100.0
    if x < ideal_low:
        return 100.0 * (x - hard_low) / (ideal_low - hard_low)
    return 100.0 * (hard_high - x) / (hard_high - ideal_high)


IDEAL_RANGES = {
    # (hard_low, ideal_low, ideal_high, hard_high)
    "hydroperiod_days": (5, 45, 150, 280),
    "inundation_depth_m": (0.02, 0.10, 0.45, 1.10),
    "inundation_frequency_pct": (3, 20, 60, 90),
    "salinity_psu": (0, 5, 35, 55),
    "connectivity_index": (0, 35, 100, 100),  # monotonic-ish, see below
}


def score_hydroperiod(days: float) -> float:
    return _trapezoid(days, *IDEAL_RANGES["hydroperiod_days"])


def score_depth(depth_m: float) -> float:
    return _trapezoid(depth_m, *IDEAL_RANGES["inundation_depth_m"])


def score_frequency(freq_pct: float) -> float:
    return _trapezoid(freq_pct, *IDEAL_RANGES["inundation_frequency_pct"])


def score_salinity(psu: float) -> float:
    return _trapezoid(psu, *IDEAL_RANGES["salinity_psu"])


def score_connectivity(index_0_100: float) -> float:
    # Roughly monotonic: more freshwater/tidal exchange is better, saturating near 100.
    lo, mid, _, _ = IDEAL_RANGES["connectivity_index"]
    if index_0_100 <= lo:
        return 0.0
    if index_0_100 >= mid:
        return min(100.0, 100.0 * (0.6 + 0.4 * index_0_100 / 100.0))
    return 100.0 * (index_0_100 - lo) / (mid - lo)


def score_elevation(elev_m: float) -> float:
    # Intertidal band assumed centred at 0.0 m local tidal datum, +/-0.6 m viable.
    return _trapezoid(elev_m, -0.9, -0.4, 0.3, 0.7)


# ---------------------------------------------------------------------------
# 3. Hard exclusion / intervention rules (section 13)
# ---------------------------------------------------------------------------

def hard_rules(site: Site, ind) -> Tuple[str, str]:
    """Returns (hard_rule_triggered, forced_classification_or_None)."""
    if ind.salinity_psu > 45 and ind.inundation_frequency_pct > 80:
        return ("Hypersaline + chronic waterlogging (salinity > 45 PSU AND inundation frequency > 80%)",
                Classification.EXCLUDE.value)
    if score_elevation(site.elevation_m) == 0.0:
        return ("Elevation outside viable intertidal envelope",
                Classification.EXCLUDE.value)
    if ind.connectivity_index < 15:
        return ("Freshwater/tidal connectivity below critical threshold (< 15)",
                Classification.INTERVENE.value)
    return ("", "")


# ---------------------------------------------------------------------------
# 4. Core scoring
# ---------------------------------------------------------------------------

def score_site_for_scenario(site: Site, scenario: str) -> Dict:
    ind = site.scenarios[scenario]
    criteria_scores = {
        "hydroperiod": score_hydroperiod(ind.hydroperiod_days),
        "depth": score_depth(ind.inundation_depth_m),
        "frequency": score_frequency(ind.inundation_frequency_pct),
        "salinity": score_salinity(ind.salinity_psu),
        "elevation": score_elevation(site.elevation_m),
        "connectivity": score_connectivity(ind.connectivity_index),
        "substrate": site.substrate_suitability,
    }
    breakdown = {
        crit: {
            "result": round(val, 1),
            "weight": WEIGHTS[crit],
            "contribution": round(val * WEIGHTS[crit], 1),
        }
        for crit, val in criteria_scores.items()
    }
    total = round(sum(v["contribution"] for v in breakdown.values()), 1)

    rule_text, forced_class = hard_rules(site, ind)

    if forced_class:
        classification = forced_class
    elif total >= 70:
        classification = Classification.PLANT.value
    elif total >= 45:
        classification = Classification.INTERVENE.value
    else:
        classification = Classification.EXCLUDE.value

    primary_constraint = min(breakdown, key=lambda c: breakdown[c]["contribution"])

    return {
        "score": total,
        "breakdown": breakdown,
        "classification": classification,
        "hard_rule": rule_text,
        "primary_constraint": CRITERION_LABELS[primary_constraint],
    }


def confidence_for_site(site: Site) -> Tuple[float, str]:
    agg = site.confidence_factors.aggregate()
    if agg >= 75:
        level = ConfidenceLevel.HIGH.value
    elif agg >= 50:
        level = ConfidenceLevel.MEDIUM.value
    else:
        level = ConfidenceLevel.LOW.value
    return round(agg, 1), level


def resilience_for_site(current_score: float, rcp45_score: float, rcp85_score: float) -> str:
    if current_score <= 0:
        return ResilienceCategory.LOW.value
    ratio = rcp85_score / current_score
    if ratio >= 0.80 and rcp45_score / current_score >= 0.85:
        return ResilienceCategory.HIGH.value
    if ratio >= 0.60:
        return ResilienceCategory.MEDIUM.value
    return ResilienceCategory.LOW.value


def overall_priority(classification: str, current_score: float, resilience: str) -> str:
    if classification == Classification.EXCLUDE.value:
        return "Exclude"
    if current_score >= 70:
        return "Priority 1" if resilience in ("High", "Medium") else "Priority 3"
    if current_score >= 45:
        return "Priority 2" if resilience in ("High", "Medium") else "Priority 3"
    return "Priority 3"


def intervention_need(hard_rule: str, classification: str, breakdown: Dict) -> str:
    if classification != Classification.INTERVENE.value:
        return "None"
    if "connectivity" in hard_rule.lower():
        return "Major"
    # Rank by how far the weakest criterion is from a passing score
    worst = min(breakdown.values(), key=lambda v: v["result"])["result"]
    return "Major" if worst < 30 else "Minor"


# ---------------------------------------------------------------------------
# 5. Apply across all sites
# ---------------------------------------------------------------------------

def apply_suitability(sites: List[Site]) -> List[Site]:
    out = []
    for site in sites:
        current = score_site_for_scenario(site, "Current")
        rcp45 = score_site_for_scenario(site, "Future 2050 (RCP4.5)")
        rcp85 = score_site_for_scenario(site, "Future 2050 (RCP8.5)")

        conf_score, conf_level = confidence_for_site(site)
        resilience = resilience_for_site(current["score"], rcp45["score"], rcp85["score"])
        priority = overall_priority(current["classification"], current["score"], resilience)
        need = intervention_need(current["hard_rule"], current["classification"], current["breakdown"])

        site.classification = current["classification"]
        site.suitability_score = current["score"]
        site.score_breakdown = current["breakdown"]
        site.primary_constraint = current["primary_constraint"]
        site.hard_rule_triggered = current["hard_rule"]

        site.confidence_score = conf_score
        site.confidence_level = conf_level

        site.future_score_rcp45 = rcp45["score"]
        site.future_score_rcp85 = rcp85["score"]
        site.resilience_category = resilience

        site.overall_priority = priority
        site.intervention_need = need

        out.append(site)
    return out

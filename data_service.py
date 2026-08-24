"""
data_service.py
----------------
Single entry point every page uses to get sites / context layers.
Caches so the (mock) pipeline only runs once per session.

Swapping mock_data.py for a real WP1-WP4 ingestion module requires no
changes here, as long as it exposes generate_sites() / generate_context_layers()
returning the same types.
"""

import pandas as pd
import streamlit as st

from mock_data import generate_sites, generate_context_layers
from suitability_engine import apply_suitability
from data_model import SCENARIOS


@st.cache_data(show_spinner="Running hydrological indicators + suitability engine...")
def load_sites():
    sites = generate_sites()
    sites = apply_suitability(sites)
    return sites


@st.cache_data
def load_context_layers():
    return generate_context_layers()


def sites_overview_df(sites) -> pd.DataFrame:
    """One row per site: everything needed for the overview map / ranking table."""
    rows = []
    for s in sites:
        rows.append({
            "site_id": s.site_id,
            "name": s.name,
            "lat": s.lat,
            "lon": s.lon,
            "area_ha": s.area_ha,
            "elevation_m": s.elevation_m,
            "existing_vegetation_pct": s.existing_vegetation_pct,
            "substrate_type": s.substrate_type,
            "classification": s.classification,
            "suitability_score": s.suitability_score,
            "primary_constraint": s.primary_constraint,
            "hard_rule_triggered": s.hard_rule_triggered,
            "confidence_score": s.confidence_score,
            "confidence_level": s.confidence_level,
            "future_score_rcp45": s.future_score_rcp45,
            "future_score_rcp85": s.future_score_rcp85,
            "resilience_category": s.resilience_category,
            "overall_priority": s.overall_priority,
            "intervention_need": s.intervention_need,
        })
    return pd.DataFrame(rows)


def scenario_indicator_df(sites, scenario: str) -> pd.DataFrame:
    """One row per site with the raw hydrological indicators for a given scenario."""
    rows = []
    for s in sites:
        ind = s.scenarios[scenario]
        rows.append({
            "site_id": s.site_id,
            "name": s.name,
            "lat": s.lat,
            "lon": s.lon,
            "classification": s.classification,
            "inundation_depth_m": ind.inundation_depth_m,
            "inundation_frequency_pct": ind.inundation_frequency_pct,
            "hydroperiod_days": ind.hydroperiod_days,
            "flow_velocity_ms": ind.flow_velocity_ms,
            "connectivity_index": ind.connectivity_index,
            "salinity_psu": ind.salinity_psu,
        })
    return pd.DataFrame(rows)


def all_scenarios_df(sites) -> pd.DataFrame:
    """Long-format table: one row per site x scenario x indicator (for comparisons)."""
    rows = []
    for s in sites:
        for scen in SCENARIOS:
            ind = s.scenarios[scen]
            rows.append({
                "site_id": s.site_id, "name": s.name, "scenario": scen,
                "inundation_depth_m": ind.inundation_depth_m,
                "inundation_frequency_pct": ind.inundation_frequency_pct,
                "hydroperiod_days": ind.hydroperiod_days,
                "flow_velocity_ms": ind.flow_velocity_ms,
                "connectivity_index": ind.connectivity_index,
                "salinity_psu": ind.salinity_psu,
            })
    return pd.DataFrame(rows)


def get_site(sites, site_id: str):
    for s in sites:
        if s.site_id == site_id:
            return s
    return None

"""
data_model.py
--------------
Core data model for the KLCRS Mangrove Restoration Decision-Support System.

The central object is `Site` (a Candidate Restoration Site), matching the
data model described in the project brief:

SITE
 |- Location, Area, Elevation, Existing vegetation, Substrate
 |- Hydrology (per scenario): depth, frequency, hydroperiod, velocity, connectivity
 |- Water quality: salinity
 |- Scenario response: Historical / Current / Dry stress / Connectivity restoration / Future climate
 |- Suitability: Plant / Intervene / Exclude
 |- Climate resilience
 |- Confidence
 |- Recommended action

This module has NO dependency on Streamlit so it can be reused by future
notebooks, batch scripts, or an API layer without dragging in the frontend.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Scenario definitions (WP2 model scenarios, section 4/10 of the brief)
# ---------------------------------------------------------------------------

SCENARIOS: List[str] = [
    "Historical",
    "Current",
    "Dry-season stress",
    "Connectivity restoration",
    "Future 2050 (RCP4.5)",
    "Future 2050 (RCP8.5)",
]

# Short labels used in compact UI elements (tables, legends)
SCENARIO_SHORT = {
    "Historical": "Historical",
    "Current": "Current",
    "Dry-season stress": "Dry stress",
    "Connectivity restoration": "Connectivity restored",
    "Future 2050 (RCP4.5)": "2050 · RCP4.5",
    "Future 2050 (RCP8.5)": "2050 · RCP8.5",
}

INDICATORS = [
    "inundation_depth_m",
    "inundation_frequency_pct",
    "hydroperiod_days",
    "flow_velocity_ms",
    "connectivity_index",
    "salinity_psu",
]

INDICATOR_LABELS = {
    "inundation_depth_m": "Inundation depth (m)",
    "inundation_frequency_pct": "Inundation frequency (%)",
    "hydroperiod_days": "Hydroperiod (days/yr)",
    "flow_velocity_ms": "Flow velocity (m/s)",
    "connectivity_index": "Freshwater connectivity index (0-100)",
    "salinity_psu": "Salinity (PSU)",
}


class Classification(str, Enum):
    PLANT = "Suitable for active planting"
    INTERVENE = "Hydrological intervention required"
    EXCLUDE = "Exclude"


CLASSIFICATION_COLOR = {
    Classification.PLANT.value: "#2E7D46",
    Classification.INTERVENE.value: "#D98F2B",
    Classification.EXCLUDE.value: "#B23A2E",
}
CLASSIFICATION_ICON = {
    Classification.PLANT.value: "🟢",
    Classification.INTERVENE.value: "🟠",
    Classification.EXCLUDE.value: "🔴",
}


class ConfidenceLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ResilienceCategory(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ---------------------------------------------------------------------------
# Supporting dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ScenarioIndicators:
    """WP2 hydrodynamic-model outputs extracted at a site, for one scenario."""
    inundation_depth_m: float
    inundation_frequency_pct: float
    hydroperiod_days: float
    flow_velocity_ms: float
    connectivity_index: float  # 0-100, higher = better freshwater/tidal exchange
    salinity_psu: float


@dataclass
class ConfidenceFactors:
    """WP1/WP3 data-quality inputs used to derive the confidence layer (section 18)."""
    dem_accuracy: float               # 0-100
    field_obs_density: float          # 0-100
    model_calibration: float          # 0-100
    salinity_obs_availability: float  # 0-100
    bathymetric_quality: float        # 0-100
    temporal_coverage: float          # 0-100
    model_obs_agreement: float        # 0-100

    def aggregate(self) -> float:
        vals = [
            self.dem_accuracy,
            self.field_obs_density,
            self.model_calibration,
            self.salinity_obs_availability,
            self.bathymetric_quality,
            self.temporal_coverage,
            self.model_obs_agreement,
        ]
        return sum(vals) / len(vals)


@dataclass
class Site:
    """A Candidate Restoration Site: the central unit of the DST."""

    site_id: str
    name: str
    lat: float
    lon: float
    area_ha: float
    elevation_m: float                 # relative to local tidal datum
    existing_vegetation_pct: float
    substrate_type: str
    substrate_suitability: float       # 0-100, from WP3 grain-size/redox/texture

    scenarios: Dict[str, ScenarioIndicators]
    confidence_factors: ConfidenceFactors

    # --- populated by suitability_engine.apply_suitability() ---
    classification: Optional[str] = None
    suitability_score: Optional[float] = None
    score_breakdown: Optional[Dict[str, Dict[str, float]]] = None
    primary_constraint: Optional[str] = None
    hard_rule_triggered: Optional[str] = None

    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None

    future_score_rcp45: Optional[float] = None
    future_score_rcp85: Optional[float] = None
    resilience_category: Optional[str] = None

    overall_priority: Optional[str] = None
    intervention_need: Optional[str] = None

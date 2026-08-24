"""
mock_data.py
------------
Synthetic stand-in for the WP1-WP4 data pipeline (georeferenced inventory,
hydrodynamic model outputs, field survey database, climate projections).

Everything here is randomly generated but internally consistent (e.g. sites
near a "hydrological barrier" get systematically lower connectivity, dry
season reduces hydroperiod/depth and raises salinity, connectivity
restoration improves hydroperiod/depth/connectivity, future-climate
scenarios raise sea level / depth / frequency).

>>> REPLACE THIS MODULE, NOT THE REST OF THE APP <<<
When real WP1-WP4 deliverables exist, write a module with the same public
functions (`generate_sites`, `generate_context_layers`) that instead reads
the project geodatabase / GeoPackage / NetCDF outputs described in the
brief, and returns the same `Site` objects. Nothing downstream needs to
change.
"""

import numpy as np

from data_model import Site, ScenarioIndicators, ConfidenceFactors, SCENARIOS

# Approximate bounding box of the Keta Lagoon Complex Ramsar Site, Ghana.
KLCRS_BOUNDS = {"lat_min": 5.79, "lat_max": 5.95, "lon_min": 0.85, "lon_max": 1.08}
KLCRS_CENTER = (
    (KLCRS_BOUNDS["lat_min"] + KLCRS_BOUNDS["lat_max"]) / 2,
    (KLCRS_BOUNDS["lon_min"] + KLCRS_BOUNDS["lon_max"]) / 2,
)

SUBSTRATES = ["Silty clay", "Sandy loam", "Organic mud", "Consolidated sand", "Peaty mud"]

N_SITES = 38


def _rng(seed=42):
    return np.random.default_rng(seed)


def _clip(x, lo, hi):
    return float(np.clip(x, lo, hi))


def generate_sites(n: int = N_SITES, seed: int = 42):
    rng = _rng(seed)
    sites = []

    # A handful of synthetic "hydrological barrier" locations that depress
    # connectivity for nearby sites (culverts / causeways / blocked channels).
    n_barriers = 5
    barrier_lat = rng.uniform(KLCRS_BOUNDS["lat_min"], KLCRS_BOUNDS["lat_max"], n_barriers)
    barrier_lon = rng.uniform(KLCRS_BOUNDS["lon_min"], KLCRS_BOUNDS["lon_max"], n_barriers)

    for i in range(n):
        site_id = f"KLCRS-{i + 1:03d}"
        lat = rng.uniform(KLCRS_BOUNDS["lat_min"], KLCRS_BOUNDS["lat_max"])
        lon = rng.uniform(KLCRS_BOUNDS["lon_min"], KLCRS_BOUNDS["lon_max"])

        # distance-to-nearest-barrier drives a "barrier effect" on connectivity
        d = np.min(np.hypot(barrier_lat - lat, barrier_lon - lon))
        barrier_effect = _clip(100 - d * 2500, 0, 85)  # closer = stronger negative effect

        area_ha = _clip(rng.gamma(3.0, 4.0), 0.5, 60)
        elevation_m = _clip(rng.normal(-0.15, 0.55), -1.6, 1.3)
        existing_veg_pct = _clip(rng.beta(1.5, 3.0) * 100, 0, 95)
        substrate_type = rng.choice(SUBSTRATES)
        substrate_suitability = _clip(rng.normal(62, 22), 5, 100)

        base_connectivity = _clip(rng.normal(48, 28) - barrier_effect * 0.75, 1, 100)
        base_hydroperiod = _clip(rng.normal(85, 68), 2, 320)
        base_depth = _clip(rng.normal(0.30, 0.24), 0.01, 1.4)
        base_frequency = _clip(rng.normal(36, 24), 1, 97)
        base_velocity = _clip(rng.normal(0.18, 0.12), 0.0, 0.95)
        base_salinity = _clip(rng.normal(24, 16), 0.5, 65)

        scenarios = {}
        for scen in SCENARIOS:
            depth, freq, hydro, vel, conn, sal = (
                base_depth, base_frequency, base_hydroperiod, base_velocity,
                base_connectivity, base_salinity,
            )
            if scen == "Historical":
                hydro *= 1.15; conn *= 1.10; sal *= 0.85
            elif scen == "Current":
                pass
            elif scen == "Dry-season stress":
                depth *= 0.45; freq *= 0.5; hydro *= 0.35; vel *= 0.5
                conn *= 0.55; sal *= 1.6
            elif scen == "Connectivity restoration":
                depth *= 1.25; freq *= 1.35; hydro *= 1.6; vel *= 1.3
                conn = _clip(conn + 30, 0, 100); sal *= 0.85
            elif scen == "Future 2050 (RCP4.5)":
                # Lower-elevation sites are disproportionately exposed to sea-level rise.
                exposure = _clip((0.25 - elevation_m) / 0.8, 0.3, 1.9)
                depth *= 1.05 + 0.22 * exposure
                freq *= 1.05 + 0.16 * exposure
                hydro *= 1.05 + 0.22 * exposure
                sal *= 1.05 + 0.10 * exposure
                conn *= 1.0 - 0.06 * exposure
            elif scen == "Future 2050 (RCP8.5)":
                exposure = _clip((0.25 - elevation_m) / 0.8, 0.3, 3.2)
                depth *= 1.10 + 0.60 * exposure
                freq *= 1.10 + 0.45 * exposure
                hydro *= 1.10 + 0.55 * exposure
                sal *= 1.10 + 0.25 * exposure
                conn *= 1.0 - 0.20 * exposure

            scenarios[scen] = ScenarioIndicators(
                inundation_depth_m=round(_clip(depth, 0.0, 2.0), 3),
                inundation_frequency_pct=round(_clip(freq, 0, 100), 1),
                hydroperiod_days=round(_clip(hydro, 0, 365), 1),
                flow_velocity_ms=round(_clip(vel, 0, 2.0), 3),
                connectivity_index=round(_clip(conn, 0, 100), 1),
                salinity_psu=round(_clip(sal, 0, 70), 1),
            )

        confidence_factors = ConfidenceFactors(
            dem_accuracy=_clip(rng.normal(70, 15), 10, 100),
            field_obs_density=_clip(rng.normal(55, 25), 0, 100),
            model_calibration=_clip(rng.normal(68, 15), 10, 100),
            salinity_obs_availability=_clip(rng.normal(50, 25), 0, 100),
            bathymetric_quality=_clip(rng.normal(60, 20), 5, 100),
            temporal_coverage=_clip(rng.normal(58, 20), 5, 100),
            model_obs_agreement=_clip(rng.normal(65, 18), 5, 100),
        )

        sites.append(Site(
            site_id=site_id,
            name=f"Site {site_id.split('-')[1]}",
            lat=round(lat, 5),
            lon=round(lon, 5),
            area_ha=round(area_ha, 2),
            elevation_m=round(elevation_m, 3),
            existing_vegetation_pct=round(existing_veg_pct, 1),
            substrate_type=substrate_type,
            substrate_suitability=round(substrate_suitability, 1),
            scenarios=scenarios,
            confidence_factors=confidence_factors,
        ))

    return sites


def generate_context_layers(seed: int = 42):
    """Boundary, existing mangrove extent, barriers, channels -- for map layers."""
    rng = _rng(seed + 1)
    b = KLCRS_BOUNDS

    # Rough lagoon boundary polygon (illustrative, not surveyed)
    boundary = [
        (b["lat_min"], b["lon_min"] + 0.03), (b["lat_min"] + 0.02, b["lon_max"] - 0.02),
        (b["lat_min"] + 0.09, b["lon_max"]), (b["lat_max"] - 0.01, b["lon_max"] - 0.05),
        (b["lat_max"], b["lon_min"] + 0.10), (b["lat_max"] - 0.05, b["lon_min"]),
        (b["lat_min"] + 0.03, b["lon_min"]), (b["lat_min"], b["lon_min"] + 0.03),
    ]

    n_mangrove = 60
    mangrove_extent = list(zip(
        rng.uniform(b["lat_min"], b["lat_max"], n_mangrove),
        rng.uniform(b["lon_min"], b["lon_max"], n_mangrove),
    ))

    n_barriers = 5
    barrier_rng = _rng(42)  # match generate_sites() barrier positions
    barriers = list(zip(
        barrier_rng.uniform(b["lat_min"], b["lat_max"], n_barriers),
        barrier_rng.uniform(b["lon_min"], b["lon_max"], n_barriers),
    ))

    # A couple of illustrative channel/tributary polylines
    channels = [
        [(b["lat_min"] + 0.01, b["lon_min"] + 0.01), (b["lat_min"] + 0.06, b["lon_min"] + 0.08),
         (b["lat_min"] + 0.12, b["lon_min"] + 0.12)],
        [(b["lat_max"] - 0.01, b["lon_max"] - 0.01), (b["lat_max"] - 0.06, b["lon_max"] - 0.10),
         (b["lat_max"] - 0.10, b["lon_max"] - 0.16)],
    ]

    return {
        "boundary": boundary,
        "mangrove_extent": mangrove_extent,
        "barriers": barriers,
        "channels": channels,
    }

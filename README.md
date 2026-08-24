# KLCRS Mangrove Restoration Decision-Support System — Python Frontend

A Streamlit application implementing the full DST architecture from the project brief:

```
WP1 (baseline) + WP3 (field) + WP4 (climate)  →  Data hub  →  WP2 (hydrodynamic model)
   → Hydrological indicators engine → Site suitability & decision engine → Decision interface
```

The candidate **Restoration Site** is the central object (see `data_model.py`), matching the
brief's data model: location/elevation/substrate, per-scenario hydrology, suitability,
climate resilience, confidence, and recommended action.

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. The sidebar groups the Overview page with six analysis
views (defined explicitly via `st.navigation` in `app.py`).

## What's real vs. placeholder right now

**Everything is running on synthetic data** so the full pipeline — indicators, the hybrid
suitability engine, confidence scoring, climate-resilience comparison, and ranking — can be
exercised end-to-end before WP1–WP4 deliverables exist. This is clearly flagged inside the
app. The suitability *logic*, UI, and module structure are real; only `mock_data.py`
is a stand-in.

## Project structure

```
klcrs_dst/
├── app.py                      # Entry point: theme, sidebar brand, grouped st.navigation
├── overview.py                  # Overview / landing page (KPIs, map, pipeline strip)
├── data_model.py                # Site / ScenarioIndicators / ConfidenceFactors dataclasses
├── mock_data.py                  # ⚠ REPLACE with real WP1–WP4 ingestion (same function signatures)
├── suitability_engine.py         # Hard rules + weighted MCDA scoring, confidence, resilience, ranking
├── data_service.py               # Cached loading + DataFrame flattening used by every page
├── ui_helpers.py                 # Theme, colour tokens, badges, sidebar brand, page header
├── map_utils.py                  # Plotly map builders (no Mapbox token required)
├── pages/
│   ├── 1_Hydrological_Conditions.py   # Hydrological conditions by indicator/scenario
│   ├── 2_Scenario_Explorer.py          # Scenario-to-scenario hydrology comparison
│   ├── 3_Restoration_Suitability.py    # Decision engine (3-level info: decision/diagnostic/scientific)
│   ├── 4_Intervention_Prioritization.py# Hydrological intervention ranking
│   ├── 5_Climate_Resilience.py         # Current vs. 2050 suitability
│   └── 6_Site_Ranking.py               # Final ranked portfolio + CSV export
└── .streamlit/config.toml        # Mangrove/lagoon colour theme
```

Page titles, icons, and sidebar grouping (Overview / Explore / Decide / Portfolio) are all
defined in `app.py` via `st.navigation`, so no numeric filename prefixes leak into the UI.

## Plugging in real data

Replace `mock_data.py` with a module that reads the actual WP1 project geodatabase /
GeoPackage, WP2 hydrodynamic model outputs (ideally time-enabled NetCDF, per the brief),
and WP3 field database, but keep the same two public functions:

- `generate_sites() -> list[Site]`
- `generate_context_layers() -> dict` (boundary, mangrove extent, barriers, channels)

Nothing else needs to change — `data_service.py` and every page consume `Site` objects,
not the mock generator directly.

## Suitability logic (transparent by design, section 12–13 of the brief)

`suitability_engine.py` implements a **hybrid framework**: hard exclusion/intervention
rules first, then a weighted multi-criteria score:

```
SI = wH·Hydroperiod + wD·Depth + wF·Frequency + wS·Salinity + wE·Elevation + wC·Connectivity + wSub·Substrate
```

Every criterion keeps its raw result, weight, and contribution so the "Diagnostic" and
"Scientific" tabs in **Restoration Suitability** can show exactly why a site was classified
the way it was — never a black-box score. All thresholds, weights, and membership ranges
are named constants at the top of the file, ready to be replaced with KLCRS-specific
ecological thresholds as WP1–WP3 evidence accumulates.

## Confidence layer (section 18)

Each site's confidence score aggregates seven data-quality factors (DEM accuracy, field
observation density, model calibration, salinity observation availability, bathymetric
quality, temporal coverage, model–observation agreement). In production these should be
computed from actual WP1/WP3 metadata rather than randomly generated.

## Known simplifications to revisit with the modelling team

- Membership-function thresholds (ideal hydroperiod/depth/salinity/elevation ranges) are
  illustrative and should be replaced with KLCRS-specific, literature- and field-validated
  values.
- The "seasonal phase" control on the Hydrological Conditions page applies an illustrative
  multiplier; once WP2 delivers time-enabled raster/NetCDF outputs it should become a real
  time slider reading actual sub-scenario time steps.
- Overall-priority logic (`suitability_engine.overall_priority`) is a simple, editable rule
  set — treat it as a first draft for stakeholder discussion, not a finished decision rule.

## Extending the frontend

- Swap the Plotly maps for a full GIS stack (e.g. `folium` + real GeoPackage layers) if
  richer cartography is needed — `map_utils.py` is the only file that would need to change.
- Add authentication / role-based views (Level 1 decision-only view for managers vs. Level 3
  scientific view for the modelling team) using `streamlit-authenticator` or your
  organisation's SSO.
- For deployment, Streamlit Community Cloud, an internal server, or a Docker container all
  work unmodified — no code changes required beyond `requirements.txt`.

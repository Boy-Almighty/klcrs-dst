"""
app.py
------
Entry point of the KLCRS Mangrove Restoration Decision-Support System.
Defines the grouped navigation and hands off to the selected page.
"""

import streamlit as st

from ui_helpers import apply_theme, sidebar_brand

st.set_page_config(page_title="KLCRS Restoration DST", page_icon="🌱", layout="wide")
apply_theme()
sidebar_brand()

overview = st.Page("overview.py", title="Overview", default=True)
hydrology = st.Page("pages/1_Hydrological_Conditions.py", title="Hydrological Conditions")
scenario = st.Page("pages/2_Scenario_Explorer.py", title="Scenario Explorer")
suitability = st.Page("pages/3_Restoration_Suitability.py", title="Restoration Suitability")
intervention = st.Page("pages/4_Intervention_Prioritization.py", title="Intervention Prioritization")
climate = st.Page("pages/5_Climate_Resilience.py", title="Climate Resilience")
ranking = st.Page("pages/6_Site_Ranking.py", title="Site Ranking")

pg = st.navigation({
    "Overview": [overview],
    "Explore": [hydrology, scenario],
    "Decide": [suitability, intervention, climate],
    "Portfolio": [ranking],
})

pg.run()

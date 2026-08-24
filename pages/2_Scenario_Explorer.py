import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_service import load_sites, all_scenarios_df, get_site
from ui_helpers import page_header
from data_model import SCENARIOS, SCENARIO_SHORT, INDICATORS, INDICATOR_LABELS

sites = load_sites()
long_df = all_scenarios_df(sites)

page_header("Scenario Explorer")

with st.container(border=True, key="klcrs_card_scenario_filter"):
    mode = st.radio("Compare", ["A single site", "Average across all sites"], horizontal=True)

    if mode == "A single site":
        ids = [s.site_id for s in sites]
        site_id = st.selectbox("Candidate site", ids,
                                format_func=lambda sid: f"{sid} — {get_site(sites, sid).name}")
        site = get_site(sites, site_id)
        st.markdown(
            f"<div class='klcrs-card' style='margin-top:0.6rem'>Area: <b>{site.area_ha} ha</b> &nbsp;|&nbsp; "
            f"Elevation: <b>{site.elevation_m} m</b> &nbsp;|&nbsp; Substrate: "
            f"<b>{site.substrate_type}</b></div>", unsafe_allow_html=True,
        )
        sub = long_df[long_df["site_id"] == site_id].set_index("scenario").loc[SCENARIOS]
    else:
        sub = long_df.groupby("scenario")[INDICATORS].mean().loc[SCENARIOS]

    indicator = st.selectbox("Indicator", INDICATORS, format_func=lambda k: INDICATOR_LABELS[k])

# Bar chart across scenarios
bar = go.Figure(go.Bar(
    x=[SCENARIO_SHORT[s] for s in SCENARIOS],
    y=sub[indicator],
    marker_color=["#8C8C8C", "#2C6E75", "#B5652E", "#2E7D46", "#D98F2B", "#B23A2E"],
    text=sub[indicator].round(2), textposition="outside",
))
bar.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10),
                   yaxis_title=INDICATOR_LABELS[indicator],
                   title=f"{INDICATOR_LABELS[indicator]} across scenarios",
                   plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
st.plotly_chart(bar, width='stretch')

# Radar chart across all indicators, normalised 0-1 per indicator for shape comparison
st.subheader("Multi-indicator scenario shape")
norm = (long_df.groupby("scenario")[INDICATORS].mean() if mode != "A single site"
        else long_df[long_df["site_id"] == site_id].set_index("scenario")[INDICATORS])
norm_all = long_df.set_index("site_id")[INDICATORS] if mode == "A single site" else long_df[INDICATORS]
ranges = {c: (norm_all[c].min(), norm_all[c].max()) for c in INDICATORS}
radar = go.Figure()
scenario_subset = st.multiselect("Scenarios to overlay", SCENARIOS,
                                  default=["Current", "Dry-season stress", "Connectivity restoration"])
for scen in scenario_subset:
    row = norm.loc[scen]
    vals = [
        0 if ranges[c][1] == ranges[c][0] else (row[c] - ranges[c][0]) / (ranges[c][1] - ranges[c][0])
        for c in INDICATORS
    ]
    radar.add_trace(go.Scatterpolar(
        r=vals + [vals[0]],
        theta=[INDICATOR_LABELS[c] for c in INDICATORS] + [INDICATOR_LABELS[INDICATORS[0]]],
        fill="toself", name=SCENARIO_SHORT[scen], opacity=0.55,
    ))
radar.update_layout(height=480, polar=dict(bgcolor="#FFFFFF", radialaxis=dict(visible=True, range=[0, 1])),
                     paper_bgcolor="#FFFFFF")
st.plotly_chart(radar, width='stretch')

with st.expander("Full indicator table for this comparison"):
    st.dataframe(sub.rename(columns=INDICATOR_LABELS).round(2), width='stretch')

st.caption(
    "Radar values are min-max normalised across "
    + ("this site's own scenarios" if mode == "A single site" else "all sites' Current scenario")
    + " so shapes are comparable — read absolute magnitudes from the bar chart or table above."
)

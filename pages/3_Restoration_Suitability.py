import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_service import load_sites, load_context_layers, sites_overview_df, get_site
from ui_helpers import (page_header, classification_badge_html,
                         confidence_badge_html, COLORS)
from map_utils import suitability_map
from suitability_engine import WEIGHTS, CRITERION_LABELS

sites = load_sites()
layers = load_context_layers()
df = sites_overview_df(sites)

page_header("Restoration Suitability")

if "selected_site" not in st.session_state:
    st.session_state.selected_site = df.iloc[0]["site_id"]

left, right = st.columns([3, 1])
with right:
    with st.container(border=True, key="klcrs_card_suitability_filter"):
        st.markdown("**Filter**")
        cls_filter = st.multiselect("Classification", df["classification"].unique().tolist(),
                                     default=df["classification"].unique().tolist())
        picked = st.selectbox("Or jump to a site", df["site_id"].tolist(),
                               index=df["site_id"].tolist().index(st.session_state.selected_site))
        if picked != st.session_state.selected_site:
            st.session_state.selected_site = picked

map_df = df[df["classification"].isin(cls_filter)]

with left:
    fig = suitability_map(map_df, layers=layers,
                           layer_flags=dict(show_boundary=True, show_mangrove=False,
                                             show_barriers=True, show_channels=False),
                           selected_id=st.session_state.selected_site)
    event = st.plotly_chart(fig, width='stretch', on_select="rerun",
                             selection_mode=("points",), key="suitability_map_chart")
    if event and event.get("selection", {}).get("points"):
        pt = event["selection"]["points"][0]
        cd = pt.get("customdata")
        if cd:
            st.session_state.selected_site = cd[0]

st.divider()

site = get_site(sites, st.session_state.selected_site)
row = df[df["site_id"] == site.site_id].iloc[0]

with st.container(border=True, key="klcrs_card_site_detail"):
    st.markdown(
        f"### {site.name} <span class='klcrs-mono'>({site.site_id})</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        classification_badge_html(site.classification) + " " +
        confidence_badge_html(site.confidence_level, site.confidence_score),
        unsafe_allow_html=True,
    )
    st.write("")

    tab_decision, tab_diagnostic, tab_scientific = st.tabs(
        [" Decision level ", " Diagnostic level ", " Scientific level "]
    )

    with tab_decision:
        st.markdown(f"#### Recommendation: **{site.classification}**")
        if site.hard_rule_triggered:
            st.info(f"Triggered by hard rule: *{site.hard_rule_triggered}*")
        else:
            st.markdown(f"Overall suitability score: **{site.suitability_score:.0f} / 100**")
        st.markdown(f"Primary constraint: **{site.primary_constraint}**")
        st.markdown(
            f"{confidence_badge_html(site.confidence_level, site.confidence_score)}  "
            f"— {'Result is well supported by current data.' if site.confidence_level=='High' else 'Additional field verification recommended before final commitment.' }",
            unsafe_allow_html=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Area", f"{site.area_ha} ha")
        c2.metric("Elevation", f"{site.elevation_m} m")
        c3.metric("Existing vegetation", f"{site.existing_vegetation_pct}%")

    with tab_diagnostic:
        st.markdown("Why this score? Every criterion's contribution to the total:")
        bd = site.score_breakdown
        bd_df = pd.DataFrame([
            {"Criterion": CRITERION_LABELS[c], "Result (0-100)": v["result"],
             "Weight": v["weight"], "Contribution": v["contribution"]}
            for c, v in bd.items()
        ]).sort_values("Contribution")

        bar = go.Figure(go.Bar(
            x=bd_df["Contribution"], y=bd_df["Criterion"], orientation="h",
            marker_color=[COLORS["exclude"] if v < WEIGHTS[c]*40 else COLORS["intervene"] if v < WEIGHTS[c]*70 else COLORS["plant"]
                          for c, v in zip(bd.keys(), bd_df["Contribution"])],
            text=bd_df["Contribution"], textposition="outside",
        ))
        bar.add_vline(x=0)
        bar.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10),
                           xaxis_title="Contribution to total score",
                           plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        st.plotly_chart(bar, width='stretch')
        st.dataframe(bd_df.set_index("Criterion"), width='stretch')
        st.markdown(f"**Total score = Σ(result × weight) = {site.suitability_score:.1f} / 100**")

    with tab_scientific:
        st.markdown("Provenance and uncertainty behind this result, for technical review.")
        meta = {
            "Scenario used for classification": "Current",
            "Model": "WP2 2D hydrodynamic model",
            "Spatial resolution": "10 m grid",
            "DEM source / accuracy": f"{site.confidence_factors.dem_accuracy:.0f}/100",
            "Field observation density": f"{site.confidence_factors.field_obs_density:.0f}/100",
            "Model calibration performance": f"{site.confidence_factors.model_calibration:.0f}/100",
            "Salinity observation availability": f"{site.confidence_factors.salinity_obs_availability:.0f}/100",
            "Bathymetric data quality": f"{site.confidence_factors.bathymetric_quality:.0f}/100",
            "Temporal coverage": f"{site.confidence_factors.temporal_coverage:.0f}/100",
            "Model-observation agreement": f"{site.confidence_factors.model_obs_agreement:.0f}/100",
            "Aggregate confidence": f"{site.confidence_score:.1f}/100 ({site.confidence_level})",
        }
        st.table(pd.DataFrame(meta.items(), columns=["Field", "Value"]).set_index("Field"))

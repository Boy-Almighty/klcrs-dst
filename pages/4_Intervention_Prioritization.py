import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data_service import load_sites, sites_overview_df, get_site
from suitability_engine import score_site_for_scenario
from ui_helpers import page_header, classification_badge_html
from data_model import Classification, INDICATOR_LABELS

sites = load_sites()
df = sites_overview_df(sites)

page_header("Hydrological Intervention Prioritization")

need_df = df[df["classification"] == Classification.INTERVENE.value].copy()

if need_df.empty:
    st.success("No candidate sites currently require hydrological intervention.")
    st.stop()

# Compute potential score after Connectivity restoration scenario
improvements = []
for sid in need_df["site_id"]:
    site = get_site(sites, sid)
    after = score_site_for_scenario(site, "Connectivity restoration")
    improvements.append({
        "site_id": sid,
        "score_before": site.suitability_score,
        "score_after": after["score"],
        "delta": round(after["score"] - site.suitability_score, 1),
        "classification_after": after["classification"],
    })
imp_df = pd.DataFrame(improvements).merge(need_df, on="site_id").sort_values("delta", ascending=False)

c1, c2, c3 = st.columns(3)
c1.metric("Sites needing intervention", len(imp_df))
c2.metric("Mean potential score gain", f"+{imp_df['delta'].mean():.1f}")
c3.metric("Would reach 'Plant' after fix", int((imp_df["classification_after"] == Classification.PLANT.value).sum()))

st.write("")
st.subheader("Ranked by potential improvement (Current → Connectivity restoration)")
bar = go.Figure()
bar.add_trace(go.Bar(name="Current", x=imp_df["site_id"], y=imp_df["score_before"], marker_color="#D98F2B"))
bar.add_trace(go.Bar(name="After connectivity restoration", x=imp_df["site_id"], y=imp_df["score_after"], marker_color="#2E7D46"))
bar.update_layout(barmode="group", height=420, margin=dict(l=10, r=10, t=20, b=10),
                   yaxis_title="Suitability score", xaxis_title="Site",
                   plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
bar.add_hline(y=70, line_dash="dot", annotation_text="Plant threshold (70)", line_color="#555")
st.plotly_chart(bar, width='stretch')

st.subheader("Intervention candidate detail")
with st.container(border=True, key="klcrs_card_intervention_detail"):
    site_id = st.selectbox("Select a site", imp_df["site_id"].tolist())
    site = get_site(sites, site_id)
    row = imp_df[imp_df["site_id"] == site_id].iloc[0]

    col1, col2 = st.columns([1, 1.4])
    with col1:
        st.markdown(classification_badge_html(site.classification), unsafe_allow_html=True)
        st.markdown(f"**Primary constraint:** {site.primary_constraint}")
        st.markdown(f"**Hard rule:** {site.hard_rule_triggered or '—'}")
        st.markdown(f"**Score:** {row['score_before']:.0f} → {row['score_after']:.0f} "
                    f"(<span style='color:#2E7D46'>+{row['delta']:.1f}</span>)", unsafe_allow_html=True)
        st.markdown(f"**Likely classification after intervention:** "
                    f"{classification_badge_html(row['classification_after'])}", unsafe_allow_html=True)
        st.info("Recommendation: restore hydrological connectivity before planting at this site.")

    with col2:
        before = site.scenarios["Current"]
        after = site.scenarios["Connectivity restoration"]
        inds = ["inundation_depth_m", "inundation_frequency_pct", "hydroperiod_days", "connectivity_index"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Without intervention", x=[INDICATOR_LABELS[i] for i in inds],
                              y=[getattr(before, i) for i in inds], marker_color="#B5652E"))
        fig.add_trace(go.Bar(name="With connectivity restored", x=[INDICATOR_LABELS[i] for i in inds],
                              y=[getattr(after, i) for i in inds], marker_color="#2C6E75"))
        fig.update_layout(barmode="group", height=360, margin=dict(l=10, r=10, t=20, b=10),
                           plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig, width='stretch')

with st.expander("Full ranked intervention table"):
    show = imp_df[["site_id", "name", "score_before", "score_after", "delta",
                    "classification_after", "primary_constraint", "confidence_level"]]
    st.dataframe(show.rename(columns={
        "score_before": "Current score", "score_after": "Score after restoration",
        "delta": "Δ score", "classification_after": "Classification after",
        "primary_constraint": "Primary constraint", "confidence_level": "Confidence",
    }).set_index("site_id"), width='stretch')

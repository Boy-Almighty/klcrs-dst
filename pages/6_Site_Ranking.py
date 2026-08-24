import plotly.graph_objects as go
import streamlit as st

from data_service import load_sites, sites_overview_df
from ui_helpers import page_header

sites = load_sites()
df = sites_overview_df(sites)

page_header("Site Ranking & Restoration Portfolio")

priority_order = {"Priority 1": 0, "Priority 2": 1, "Priority 3": 2, "Exclude": 3}
df = df.copy()
df["priority_rank"] = df["overall_priority"].map(priority_order)
df = df.sort_values(["priority_rank", "suitability_score"], ascending=[True, False]).reset_index(drop=True)
df.insert(0, "rank", range(1, len(df) + 1))

with st.container(border=True, key="klcrs_card_ranking_filter"):
    c1, c2 = st.columns(2)
    with c1:
        priority_filter = st.multiselect("Overall priority", df["overall_priority"].unique().tolist(),
                                          default=df["overall_priority"].unique().tolist())
    with c2:
        min_conf = st.slider("Minimum confidence score", 0, 100, 0)

filtered = df[(df["overall_priority"].isin(priority_filter)) & (df["confidence_score"] >= min_conf)]

st.write("")
st.subheader("Ranked portfolio")
display_cols = ["rank", "site_id", "name", "classification", "suitability_score",
                 "intervention_need", "resilience_category", "confidence_level", "overall_priority"]
pretty = filtered[display_cols].rename(columns={
    "site_id": "Site", "name": "Name", "classification": "Classification",
    "suitability_score": "Suitability score", "intervention_need": "Intervention need",
    "resilience_category": "Climate resilience", "confidence_level": "Confidence",
    "overall_priority": "Overall priority", "rank": "Rank",
})
st.dataframe(pretty.set_index("Rank"), width='stretch', height=460)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download portfolio as CSV", csv, "klcrs_restoration_portfolio.csv", "text/csv")

st.subheader("Top sites by suitability score")
top_n = st.slider("Show top N sites", 5, min(30, len(filtered)) if len(filtered) >= 5 else 5, min(15, len(filtered)) if len(filtered) else 5)
top = filtered.head(top_n)
colors = {"Priority 1": "#2E7D46", "Priority 2": "#D98F2B", "Priority 3": "#8A6D3B", "Exclude": "#B23A2E"}
fig = go.Figure(go.Bar(
    x=top["suitability_score"], y=top["site_id"], orientation="h",
    marker_color=[colors.get(p, "#666") for p in top["overall_priority"]],
    text=top["overall_priority"], textposition="outside",
))
fig.update_layout(height=max(320, 26 * len(top)), margin=dict(l=10, r=10, t=10, b=10),
                   xaxis_title="Suitability score", yaxis=dict(autorange="reversed"),
                   plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
st.plotly_chart(fig, width='stretch')

st.caption(
    "**Overall priority** combines current suitability with climate resilience: high current "
    "suitability and resilience under 2050 projections → Priority 1; moderate suitability or "
    "resilience → Priority 2; high suitability but low future resilience, or generally low "
    "suitability → Priority 3; hard-excluded sites → Exclude."
)

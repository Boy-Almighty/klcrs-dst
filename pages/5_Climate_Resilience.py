import plotly.graph_objects as go
import streamlit as st

from data_service import load_sites, sites_overview_df
from ui_helpers import page_header
from data_model import ResilienceCategory

sites = load_sites()
df = sites_overview_df(sites)

page_header("Climate Resilience")

res_filter = st.multiselect("Resilience category", [c.value for c in ResilienceCategory],
                             default=[c.value for c in ResilienceCategory])
view = df[df["resilience_category"].isin(res_filter)]

c1, c2, c3 = st.columns(3)
for c, cat, color in zip((c1, c2, c3), ["High", "Medium", "Low"], ["#2E7D46", "#D98F2B", "#B23A2E"]):
    n = (df["resilience_category"] == cat).sum()
    c.metric(f"{cat} resilience", int(n))

st.write("")
st.subheader("Current vs. future (2050, RCP8.5) suitability")
fig = go.Figure()
colors = {"High": "#2E7D46", "Medium": "#D98F2B", "Low": "#B23A2E"}
for cat in ["High", "Medium", "Low"]:
    sub = view[view["resilience_category"] == cat]
    if sub.empty:
        continue
    fig.add_trace(go.Scatter(
        x=sub["suitability_score"], y=sub["future_score_rcp85"], mode="markers",
        marker=dict(size=11, color=colors[cat]),
        name=f"{cat} resilience",
        text=sub["site_id"], hovertemplate="%{text}<br>Current: %{x}<br>2050 RCP8.5: %{y}<extra></extra>",
    ))
fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(dash="dot", color="#999"))
fig.add_vline(x=70, line_dash="dot", line_color="#bbb")
fig.add_hline(y=70, line_dash="dot", line_color="#bbb")
fig.add_annotation(x=90, y=95, text="Priority investment", showarrow=False, font=dict(color="#2E7D46"))
fig.add_annotation(x=90, y=35, text="Short-term win, higher long-term risk", showarrow=False, font=dict(color="#B23A2E"))
fig.add_annotation(x=25, y=90, text="Emerging opportunity (2050)", showarrow=False, font=dict(color="#2C6E75"))
fig.update_layout(height=520, xaxis_title="Current suitability score", yaxis_title="2050 (RCP8.5) suitability score",
                   xaxis=dict(range=[0, 100]), yaxis=dict(range=[0, 100]), margin=dict(l=10, r=10, t=20, b=10),
                   plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
st.plotly_chart(fig, width='stretch')

st.subheader("Scenario comparison table")
table = view[["site_id", "name", "suitability_score", "future_score_rcp45", "future_score_rcp85",
              "resilience_category", "classification"]].sort_values("suitability_score", ascending=False)
st.dataframe(table.rename(columns={
    "suitability_score": "Current", "future_score_rcp45": "2050 · RCP4.5",
    "future_score_rcp85": "2050 · RCP8.5", "resilience_category": "Resilience",
    "classification": "Current classification",
}).set_index("site_id"), width='stretch', height=420)

st.caption(
    "Resilience category compares the 2050 RCP8.5 score against the current score: **High** "
    "(retains ≥80% of current suitability under RCP8.5 and ≥85% under RCP4.5), **Medium** "
    "(retains ≥50% under RCP8.5), otherwise **Low**."
)

import streamlit as st
import plotly.express as px

from data_service import load_sites, load_context_layers, scenario_indicator_df
from ui_helpers import page_header
from map_utils import indicator_map
from data_model import SCENARIOS, INDICATOR_LABELS

sites = load_sites()
layers = load_context_layers()

page_header("Hydrological Conditions")

with st.container(border=True, key="klcrs_card_hydro_filter"):
    c1, c2, c3 = st.columns([1.3, 1.3, 1])
    with c1:
        indicator = st.selectbox("Indicator", options=list(INDICATOR_LABELS.keys()),
                                  format_func=lambda k: INDICATOR_LABELS[k])
    with c2:
        scenario = st.selectbox("Scenario", options=SCENARIOS, index=1)
    with c3:
        phase = st.select_slider(
            "Seasonal phase",
            options=["Dry season", "Wet season", "Flood peak", "Recession"],
            value="Wet season",
            help="Applies a seasonal multiplier to the selected indicator.",
        )

PHASE_MULT = {
    "Dry season": {"inundation_depth_m": 0.6, "inundation_frequency_pct": 0.6, "hydroperiod_days": 1.0,
                   "flow_velocity_ms": 0.6, "connectivity_index": 0.8, "salinity_psu": 1.3},
    "Wet season": {"inundation_depth_m": 1.0, "inundation_frequency_pct": 1.0, "hydroperiod_days": 1.0,
                   "flow_velocity_ms": 1.0, "connectivity_index": 1.0, "salinity_psu": 1.0},
    "Flood peak": {"inundation_depth_m": 1.6, "inundation_frequency_pct": 1.3, "hydroperiod_days": 1.0,
                   "flow_velocity_ms": 1.8, "connectivity_index": 1.1, "salinity_psu": 0.7},
    "Recession": {"inundation_depth_m": 0.85, "inundation_frequency_pct": 0.9, "hydroperiod_days": 1.0,
                  "flow_velocity_ms": 0.7, "connectivity_index": 0.95, "salinity_psu": 1.1},
}

df = scenario_indicator_df(sites, scenario)
mult = PHASE_MULT[phase][indicator]
df[indicator] = (df[indicator] * mult).round(2)
if indicator in ("connectivity_index", "inundation_frequency_pct"):
    df[indicator] = df[indicator].clip(upper=100)

st.write("")
left, right = st.columns([3, 1])
with right:
    with st.container(border=True, key="klcrs_card_hydro_layers"):
        show_boundary = st.checkbox("KLCRS boundary", value=True)
        show_mangrove = st.checkbox("Existing mangrove extent", value=False)
        show_barriers = st.checkbox("Hydrological barriers", value=True)
    st.write("")
    st.metric(f"Mean {INDICATOR_LABELS[indicator]}", f"{df[indicator].mean():.2f}")
    st.metric("Range", f"{df[indicator].min():.2f} – {df[indicator].max():.2f}")

with left:
    fig = indicator_map(
        df, indicator, INDICATOR_LABELS[indicator], layers=layers,
        layer_flags=dict(show_boundary=show_boundary, show_mangrove=show_mangrove,
                          show_barriers=show_barriers, show_channels=False),
    )
    st.plotly_chart(fig, width='stretch')

st.subheader("Distribution across candidate sites")
hist = px.histogram(df, x=indicator, nbins=20, color_discrete_sequence=["#2C6E75"])
hist.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_title=INDICATOR_LABELS[indicator], yaxis_title="Number of sites",
                    plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
st.plotly_chart(hist, width='stretch')

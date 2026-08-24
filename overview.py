"""
overview.py
-----------
Landing view of the KLCRS Mangrove Restoration Decision-Support System.
Registered as the default page in app.py's st.navigation().
"""

import streamlit as st

from data_service import load_sites, load_context_layers, sites_overview_df
from ui_helpers import status_pill, COLORS
from map_utils import suitability_map
from data_model import Classification

sites = load_sites()
layers = load_context_layers()
df = sites_overview_df(sites)

with st.container(border=True, key="klcrs_card_page_header"):
    header_l, header_r = st.columns([5, 2])
    with header_l:
        st.title("Mangrove Restoration Overview")
    with header_r:
        st.write("")
        st.write("")
        status_pill("Synthetic demo dataset")
st.write("")



# --- KPIs ---
n_total = len(df)
n_plant = (df["classification"] == Classification.PLANT.value).sum()
n_intervene = (df["classification"] == Classification.INTERVENE.value).sum()
n_exclude = (df["classification"] == Classification.EXCLUDE.value).sum()
mean_conf = df["confidence_score"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Candidate sites", n_total)
k2.metric("🟢 Suitable for planting", int(n_plant))
k3.metric("🟠 Need intervention", int(n_intervene))
k4.metric("🔴 Excluded", int(n_exclude))
k5.metric("Mean confidence", f"{mean_conf:.0f}/100")

st.write("")

# --- Overview map ---
st.subheader("Site overview map")
left, right = st.columns([3, 1])
with right:
    with st.container(border=True, key="klcrs_card_maplayers"):
        st.markdown("**Map layers**")
        show_boundary = st.checkbox("KLCRS boundary", value=True)
        show_mangrove = st.checkbox("Existing mangrove extent", value=True)
        show_barriers = st.checkbox("Hydrological barriers", value=True)
        show_channels = st.checkbox("Channels / tributaries", value=False)
        st.markdown("---")
        st.markdown("**Legend**")
        st.markdown("🟢 Suitable for active planting")
        st.markdown("🟠 Hydrological intervention required")
        st.markdown("🔴 Exclude")

with left:
    fig = suitability_map(
        df, layers=layers,
        layer_flags=dict(show_boundary=show_boundary, show_mangrove=show_mangrove,
                          show_barriers=show_barriers, show_channels=show_channels),
    )
    st.plotly_chart(fig, width='stretch')

st.caption(
    "Classification uses the **Current** scenario. Open **Restoration Suitability** to inspect "
    "why a site was classified this way, or **Scenario Explorer** to see how its hydrology "
    "shifts across management scenarios."
)

with st.expander("What each section covers"):
    st.markdown("""
| Section | What it shows |
|---|---|
| **Overview** | Where candidate sites sit relative to the lagoon, mangroves, and barriers |
| **Hydrological Conditions** | The hydrological conditions each site experiences today |
| **Scenario Explorer** | How a site's hydrology changes under a different management scenario |
| **Restoration Suitability** | Whether to plant, intervene first, or exclude a site — and why |
| **Intervention Prioritization** | Where a hydrological fix would unlock the most restoration potential |
| **Climate Resilience** | Whether a site suitable today will still work in 2050 |
| **Site Ranking** | The prioritised restoration portfolio |
""")

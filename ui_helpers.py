"""
ui_helpers.py
-------------
Shared design system so every page looks and behaves the same way.

- apply_theme(): fonts, colour tokens, and the global CSS layer (sidebar
  navigation, elevated cards, KPI stat tiles, typography).
- kpi_row(): a row of stat cards with an icon accent, mirroring a modern
  analytics-dashboard summary strip.
- classification_badge(), confidence_badge(), priority_badge(): the
  recurring "pill" used wherever a site's status is shown.
- page_header(): page title in its own elevated container at the top of the page.
- sidebar_brand(): the mark shown above the navigation menu.
"""

import streamlit as st

from data_model import CLASSIFICATION_COLOR, CLASSIFICATION_ICON

# Design tokens -------------------------------------------------------------
COLORS = {
    "canopy": "#1F4B3F",       # deep mangrove green - primary
    "canopy_dark": "#15332A",  # sidebar background
    "lagoon": "#2C6E75",       # tidal teal - secondary / accent
    "sand": "#F6F3EA",         # (legacy) warm background tone, no longer used for app bg
    "paper": "#FFFFFF",        # app background + card surfaces
    "border": "#E7E2D4",       # hairline borders on light surfaces
    "clay": "#B5652E",         # warm accent
    "ink": "#1C2B24",          # body text
    "muted": "#647169",        # secondary / caption text
    "plant": "#2E7D46",
    "intervene": "#D98F2B",
    "exclude": "#B23A2E",
    "confidence_high": "#1F4B3F",
    "confidence_medium": "#8A7A2E",
    "confidence_low": "#8C4A2F",
}


def apply_theme():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
        color: {COLORS['ink']};
    }}
    h1, h2, h3 {{
        font-family: 'Fraunces', serif;
        font-weight: 600;
        color: {COLORS['canopy']};
        letter-spacing: -0.01em;
    }}
    p, li {{ color: {COLORS['ink']}; }}

    /* ---------- App shell ---------- */
    .stApp {{ background: {COLORS['paper']}; }}
    div.block-container {{ padding-top: 2.2rem; max-width: 1280px; }}
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    header[data-testid="stHeader"] {{ background: transparent; }}

    /* ---------- Shared 3D elevation shadow ----------
       Layered shadow (contact + ambient + long throw) so every card reads as
       raised off the white page instead of flat. */
    :root {{
        --klcrs-elevation: 0 1px 0 rgba(20,30,25,0.05),
                            0 2px 4px rgba(20,30,25,0.06),
                            0 10px 22px rgba(20,30,25,0.09),
                            0 22px 40px rgba(20,30,25,0.06);
        --klcrs-elevation-hover: 0 1px 0 rgba(20,30,25,0.05),
                            0 4px 8px rgba(20,30,25,0.08),
                            0 16px 30px rgba(20,30,25,0.11),
                            0 28px 48px rgba(20,30,25,0.07);
        /* dark-surface variant: inset highlight along the top edge (catches
           light) plus a grounding drop shadow, for cards on the dark sidebar */
        --klcrs-elevation-dark: 0 1px 0 rgba(255,255,255,0.07) inset,
                            0 3px 6px rgba(0,0,0,0.30),
                            0 10px 20px rgba(0,0,0,0.30);
    }}

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {{
        background: {COLORS['canopy_dark']};
        border-right: none;
    }}
    [data-testid="stSidebar"] * {{ color: #E9EFEA; }}
    [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.12); }}

    [data-testid="stSidebarNav"] {{ padding-top: 0.25rem; }}
    /* Streamlit always inserts its auto-generated page nav first in the DOM.
       Reorder via flexbox so our brand mark visually sits above it instead. */
    [data-testid="stSidebarContent"] {{
        display: flex !important;
        flex-direction: column !important;
    }}
    [data-testid="stSidebarHeader"] {{ order: 0; }}
    [data-testid="stSidebarUserContent"] {{ order: 1; }}
    [data-testid="stSidebarNav"] {{ order: 2; }}

    /* Each nav section (its header label + the links under it) becomes its
       own raised panel, matching the elevated-card look used everywhere else. */
    [data-testid="stSidebarNavItems"] > div {{
        background: rgba(255,255,255,0.045);
        border-radius: 12px;
        margin: 0.35rem 0.55rem 0.6rem 0.55rem;
        padding: 0.3rem 0.25rem 0.5rem 0.25rem;
        box-shadow: var(--klcrs-elevation-dark);
    }}
    header[data-testid="stNavSectionHeader"] {{
        padding: 0.3rem 0.55rem 0.2rem 0.55rem !important;
    }}
    header[data-testid="stNavSectionHeader"] p {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: rgba(233,239,234,0.6) !important;
        font-weight: 500;
        margin: 0;
    }}
    [data-testid="stSidebarNav"] a {{
        border-radius: 8px;
        margin: 0.05rem 0.3rem;
        padding: 0.5rem 0.7rem !important;
        color: rgba(233,239,234,0.82) !important;
        font-weight: 500;
        transition: background 0.15s ease, box-shadow 0.15s ease;
    }}
    [data-testid="stSidebarNav"] a:hover {{
        background: rgba(255,255,255,0.09);
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{
        background: {COLORS['lagoon']};
        color: #FFFFFF !important;
        font-weight: 600;
        box-shadow: 0 1px 0 rgba(255,255,255,0.18) inset, 0 3px 8px rgba(0,0,0,0.35);
    }}
    [data-testid="stSidebarNav"] span {{ color: inherit !important; }}

    /* ---------- Sidebar brand mark ---------- */
    .klcrs-brand {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.9rem 0.9rem 1.1rem 0.9rem;
        margin-bottom: 0.2rem;
        border-bottom: 1px solid rgba(255,255,255,0.12);
    }}
    .klcrs-brand-mark {{
        width: 36px; height: 36px;
        border-radius: 10px;
        background: {COLORS['lagoon']};
        display: flex; align-items: center; justify-content: center;
        font-size: 1.15rem;
        flex-shrink: 0;
    }}
    .klcrs-brand-name {{
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 1.05rem;
        color: #FFFFFF;
        line-height: 1.15;
    }}
    .klcrs-brand-sub {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: rgba(233,239,234,0.55);
    }}

    /* ---------- Page header ---------- */
    .st-key-klcrs_card_page_header h1 {{ margin: 0; }}

    /* ---------- Status pill (data provenance) ---------- */
    .klcrs-status-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: {COLORS['paper']};
        border: 1px solid {COLORS['border']};
        border-radius: 999px;
        padding: 0.3rem 0.85rem;
        font-size: 0.8rem;
        color: {COLORS['muted']};
        font-weight: 500;
    }}
    .klcrs-status-dot {{
        width: 7px; height: 7px; border-radius: 50%;
        background: {COLORS['clay']};
        display: inline-block;
    }}

    /* ---------- Badges ---------- */
    .klcrs-badge {{
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
        color: white;
        margin-right: 0.35rem;
    }}

    /* ---------- Generic elevated card ---------- */
    .klcrs-card {{
        background: {COLORS['paper']};
        border-radius: 14px;
        padding: 1.1rem 1.3rem;
        border: 1px solid {COLORS['border']};
        box-shadow: var(--klcrs-elevation);
        margin-bottom: 0.8rem;
    }}
    .klcrs-mono {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.85rem;
        color: {COLORS['lagoon']};
    }}

    /* ---------- Native bordered containers as cards ----------
       Streamlit's internal border-wrapper testid varies by version, so every
       st.container(border=True) in this app is given an explicit key
       ("klcrs_card_...") and targeted via its stable st-key-* class instead. */
    div[data-testid="stVerticalBlockBorderWrapper"],
    [class*="st-key-klcrs_card_"] {{
        background: {COLORS['paper']} !important;
        border-radius: 14px !important;
        border: 1px solid {COLORS['border']} !important;
        box-shadow: var(--klcrs-elevation) !important;
    }}

    /* ---------- KPI stat tiles (st.metric) ---------- */
    div[data-testid="stMetric"] {{
        background: {COLORS['paper']};
        border-radius: 14px;
        border: 1px solid {COLORS['border']};
        border-left: 4px solid {COLORS['lagoon']};
        padding: 0.85rem 1rem 0.7rem 1rem;
        box-shadow: var(--klcrs-elevation);
    }}
    div[data-testid="stMetricValue"] {{
        color: {COLORS['canopy']};
        font-family: 'Fraunces', serif;
        font-size: 1.7rem;
    }}
    div[data-testid="stMetricLabel"] {{
        color: {COLORS['muted']};
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}

    /* ---------- Tables / dataframes ---------- */
    div[data-testid="stDataFrame"] {{
        background: {COLORS['paper']};
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {COLORS['border']};
        box-shadow: var(--klcrs-elevation);
    }}

    div[data-testid="stTable"] {{
        background: {COLORS['paper']};
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {COLORS['border']};
        box-shadow: var(--klcrs-elevation);
        padding: 0.2rem 0.6rem;
    }}
    div[data-testid="stTable"] table {{ background: {COLORS['paper']}; }}

    /* ---------- Charts / maps ---------- */
    div[data-testid="stPlotlyChart"] {{
        background: {COLORS['paper']};
        border-radius: 14px;
        border: 1px solid {COLORS['border']};
        box-shadow: var(--klcrs-elevation);
        padding: 0.9rem;
    }}

    /* ---------- Expanders ---------- */
    div[data-testid="stExpander"] {{
        background: {COLORS['paper']};
        border-radius: 14px;
        border: 1px solid {COLORS['border']} !important;
        box-shadow: var(--klcrs-elevation);
        overflow: hidden;
    }}
    div[data-testid="stExpander"] summary {{
        background: {COLORS['paper']};
    }}

    /* ---------- Tabs ---------- */
    button[data-testid="stTab"] {{
        font-weight: 600;
    }}

    /* ---------- Section subheaders ---------- */
    h3 {{ margin-top: 0.4rem; }}
    </style>
    """, unsafe_allow_html=True)


def sidebar_brand():
    """Small brand mark shown above the auto-generated page navigation."""
    st.sidebar.markdown(
        "<div class='klcrs-brand'>"
        "<div class='klcrs-brand-mark'>🌱</div>"
        "<div><div class='klcrs-brand-name'>KLCRS DST</div>"
        "<div class='klcrs-brand-sub'>Restoration Intelligence</div></div>"
        "</div>",
        unsafe_allow_html=True,
    )


def page_header(title: str):
    """Page title, kept at the top of the page in its own elevated container."""
    with st.container(border=True, key="klcrs_card_page_header"):
        st.title(title)
    st.write("")


def status_pill(text: str):
    st.markdown(
        f"<span class='klcrs-status-pill'><span class='klcrs-status-dot'></span>{text}</span>",
        unsafe_allow_html=True,
    )


def classification_badge_html(classification: str) -> str:
    color = CLASSIFICATION_COLOR.get(classification, "#666")
    icon = CLASSIFICATION_ICON.get(classification, "")
    return f"<span class='klcrs-badge' style='background:{color}'>{icon} {classification}</span>"


def confidence_badge_html(level: str, score: float) -> str:
    color = {
        "High": COLORS["confidence_high"],
        "Medium": COLORS["confidence_medium"],
        "Low": COLORS["confidence_low"],
    }.get(level, "#666")
    return f"<span class='klcrs-badge' style='background:{color}'>Confidence: {level} ({score:.0f}/100)</span>"


def priority_badge_html(priority: str) -> str:
    color = {
        "Priority 1": COLORS["plant"],
        "Priority 2": COLORS["intervene"],
        "Priority 3": "#8A6D3B",
        "Exclude": COLORS["exclude"],
    }.get(priority, "#666")
    return f"<span class='klcrs-badge' style='background:{color}'>{priority}</span>"

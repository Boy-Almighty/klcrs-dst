"""
map_utils.py
------------
All Plotly map construction lives here so every page renders maps the same
way. Uses the free 'open-street-map' style (no Mapbox token required).
"""

import plotly.graph_objects as go

from data_model import CLASSIFICATION_COLOR
from mock_data import KLCRS_CENTER


def _base_layout(fig, zoom=10.6):
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=KLCRS_CENTER[0], lon=KLCRS_CENTER[1]),
            zoom=zoom,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=560,
        legend=dict(
            x=0.01, y=0.99, xanchor="left", yanchor="top",
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(28,43,36,0.15)", borderwidth=1,
        ),
    )
    return fig


def add_context_layers(fig, layers: dict, show_boundary=True, show_mangrove=True,
                        show_barriers=True, show_channels=True):
    if show_boundary and layers.get("boundary"):
        lat, lon = zip(*(layers["boundary"] + [layers["boundary"][0]]))
        fig.add_trace(go.Scattermapbox(
            lat=lat, lon=lon, mode="lines",
            line=dict(width=2, color="#2C6E75"),
            name="KLCRS boundary (indicative)", hoverinfo="name",
        ))

    if show_mangrove and layers.get("mangrove_extent"):
        lat, lon = zip(*layers["mangrove_extent"])
        fig.add_trace(go.Scattermapbox(
            lat=lat, lon=lon, mode="markers",
            marker=dict(size=5, color="#4C8C5A", opacity=0.55),
            name="Existing mangrove extent (illustrative)", hoverinfo="name",
        ))

    if show_channels and layers.get("channels"):
        for i, ch in enumerate(layers["channels"]):
            lat, lon = zip(*ch)
            fig.add_trace(go.Scattermapbox(
                lat=lat, lon=lon, mode="lines",
                line=dict(width=3, color="#3A7CA5"),
                name="Channel / tributary" if i == 0 else None,
                showlegend=(i == 0), hoverinfo="name",
            ))

    if show_barriers and layers.get("barriers"):
        lat, lon = zip(*layers["barriers"])
        fig.add_trace(go.Scattermapbox(
            lat=lat, lon=lon, mode="markers",
            marker=dict(size=13, color="#B23A2E", symbol="circle"),
            name="Hydrological barrier", hoverinfo="name",
        ))
    return fig


def suitability_map(df, layers=None, layer_flags=None, selected_id=None):
    """Overview / Suitability style map coloured by Plant/Intervene/Exclude."""
    fig = go.Figure()
    if layers and layer_flags:
        add_context_layers(fig, layers, **layer_flags)

    for cls, color in CLASSIFICATION_COLOR.items():
        sub = df[df["classification"] == cls]
        if sub.empty:
            continue
        sizes = [16 if sid == selected_id else 10 for sid in sub["site_id"]]
        fig.add_trace(go.Scattermapbox(
            lat=sub["lat"], lon=sub["lon"], mode="markers",
            marker=dict(size=sizes, color=color),
            name=cls,
            customdata=sub[["site_id", "name", "suitability_score"]],
            hovertemplate="<b>%{customdata[1]} (%{customdata[0]})</b><br>Score: %{customdata[2]}<extra></extra>",
        ))
    return _base_layout(fig)


def indicator_map(df, indicator_col: str, label: str, layers=None, layer_flags=None):
    """Hydrological Conditions style map: continuous colour scale for one indicator."""
    fig = go.Figure()
    if layers and layer_flags:
        add_context_layers(fig, layers, **layer_flags)

    fig.add_trace(go.Scattermapbox(
        lat=df["lat"], lon=df["lon"], mode="markers",
        marker=dict(
            size=12,
            color=df[indicator_col],
            colorscale="Teal",
            showscale=True,
            colorbar=dict(title=label, thickness=14),
        ),
        customdata=df[["site_id", "name", indicator_col]],
        hovertemplate="<b>%{customdata[1]} (%{customdata[0]})</b><br>" + label + ": %{customdata[2]}<extra></extra>",
        name=label,
    ))
    return _base_layout(fig)

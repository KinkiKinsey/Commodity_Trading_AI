import pandas as pd
import numpy as np
import webbrowser
from typing import Optional
import plotly.express as px

import dash
from dash import dcc, html, Input, Output


def run_oil_metrics_treemap(
    queries_df: pd.DataFrame,
    host: str = "127.0.0.1",
    port: int = 8050,
    open_browser: bool = True
) -> None:
    """
    Launch an in-memory Dash app to visualize Oil Metrics queries_df as an interactive treemap.

    Treemap:
    - Hierarchy: factor -> factor time
    - Size: abs(weighted_mean)
    - Click a node to focus; click a time node to show details (driver_type, AI_Reason, dates).

    Args:
        queries_df: DataFrame containing columns:
            factor or factor_name, weighted_mean, time_interval or (start_date/end_date),
            driver_type, AI_Reason, duration_days, and other numeric columns.
        host: Server host (default: 127.0.0.1)
        port: Server port (default: 8050)
        open_browser: Open default browser when server starts.
    """

    if queries_df is None or len(queries_df) == 0:
        raise ValueError("queries_df is empty or None")

    df = queries_df.copy()

    # Normalize factor column
    if "factor_name" in df.columns:
        df["factor_display"] = df["factor_name"].astype(str)
    elif "factor" in df.columns:
        df["factor_display"] = df["factor"].astype(str)
    else:
        df["factor_display"] = "UNKNOWN"

    # Build a time label
    def _time_label(row):
        ti = str(row.get("time_interval", "") or "").strip()
        if ti:
            return ti
        start_date = row.get("start_date")
        end_date = row.get("end_date")
        if start_date and end_date:
            return f"{start_date} → {end_date}"
        return "Unknown interval"

    df["time_label"] = df.apply(_time_label, axis=1)

    # Size encoding by absolute impact
    def _impact_size(v) -> float:
        try:
            return float(abs(float(v)))
        except Exception:
            return 0.0

    if "weighted_mean" not in df.columns:
        df["weighted_mean"] = 0.0
    df["impact_size"] = df["weighted_mean"].apply(_impact_size)

    # Minimal numeric hygiene
    for col in ("weighted_variance", "risk_reward_ratio", "trend_count", "duration_days"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Build initial figure
    fig = px.treemap(
        df,
        path=["factor_display", "time_label"],
        values="impact_size",
        color="impact_size",
        color_continuous_scale=["#d6f5f0", "#6bd0c7", "#2a8f86", "#166a65"],
        hover_data={
            "factor_display": True,
            "time_label": True,
            "impact_size": ":.4f",
            "weighted_mean": ":.4f" if df["weighted_mean"].notna().any() else False,
        },
    )
    fig.update_layout(margin=dict(t=20, r=10, l=10, b=10))

    app = dash.Dash(__name__)

    app.layout = html.Div(
        style={"background": "#0e0f10", "color": "#eaeaea", "fontFamily": "Inter, system-ui, sans-serif", "padding": 12},
        children=[
            html.H3("Oil Metrics Treemap", style={"margin": "8px 0 12px"}),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "2fr 1fr", "gap": 12, "alignItems": "start"},
                children=[
                    dcc.Graph(id="treemap", figure=fig, style={"height": "78vh", "background": "#0e0f10"}),
                    html.Div(
                        id="detail_panel",
                        style={"background": "#151718", "border": "1px solid #2b2f31", "borderRadius": 8, "padding": 12, "minHeight": "78vh"},
                        children=[
                            html.Div("Click a time node to see details", style={"opacity": 0.75}),
                        ],
                    ),
                ],
            ),
        ],
    )

    @app.callback(Output("detail_panel", "children"), Input("treemap", "clickData"))
    def show_details(clickData):
        if not clickData:
            return [html.Div("Click a time node to see details", style={"opacity": 0.75})]
        p = clickData.get("points", [{}])[0]
        # The leaf node label is our time_label; parent is factor
        label = p.get("label")
        parent = p.get("parent")
        # If user clicked a factor node (no parent or parent is root), prompt
        if label and (parent is None or parent == "Oil Metrics"):
            return [
                html.Div(
                    [html.Div("Factor selected", style={"fontWeight": 700, "marginBottom": 6}), html.Div(str(label))]
                )
            ]

        # Try to match one row by factor_display + time_label
        try:
            mask = (df["factor_display"].astype(str) == str(parent)) & (df["time_label"].astype(str) == str(label))
            row = df.loc[mask].iloc[0].to_dict()
        except Exception:
            return [html.Div("No matching row for selection", style={"opacity": 0.75})]

        def field(label_txt: str, value_key: str):
            val = row.get(value_key, None)
            if val is None or val == "":
                return None
            return html.Div([html.B(f"{label_txt}: "), html.Span(str(val))], style={"marginBottom": 6})

        cards = [
            html.Div("Selection Details", style={"fontWeight": 800, "marginBottom": 8, "fontSize": 16}),
            field("Factor", "factor_display"),
            field("Interval", "time_label"),
            field("Impact |weighted_mean|", "impact_size"),
            field("Driver Type", "driver_type"),
            field("AI_Reason", "AI_Reason"),
            field("Start", "start_date"),
            field("End", "end_date"),
            field("Duration (days)", "duration_days"),
            field("Risk/Reward", "risk_reward_ratio"),
            field("Weighted Variance", "weighted_variance"),
            field("Trend Count", "trend_count"),
        ]
        return [c for c in cards if c is not None]

    url = f"http://{host}:{port}"
    if open_browser:
        try:
            webbrowser.open_new(url)
        except Exception:
            pass

    # Dash >=2.16 uses app.run (run_server is obsolete)
    app.run(host=host, port=port, debug=False)



from __future__ import annotations

from typing import Optional

import altair as alt
import streamlit as st


PALETTE = {
    "bg": "#050505",
    "panel": "#111213",
    "panel_2": "#17191b",
    "border": "#26282b",
    "text": "#f4f4f1",
    "muted": "#8e9499",
    "dim": "#5c6268",
    "green": "#19e58c",
    "yellow": "#f2d24b",
    "red": "#ff4f4f",
    "cyan": "#5ad7ff",
    "purple": "#9a7dff",
}


CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"], .stMarkdown, .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}}

.stApp {{
    background:
        radial-gradient(circle at 80% -10%, rgba(25,229,140,0.10), transparent 34rem),
        linear-gradient(180deg, #070808 0%, #050505 48%, #050505 100%);
    color: {PALETTE["text"]};
}}

.block-container {{
    max-width: 1440px;
    padding-top: 1.25rem;
    padding-bottom: 3rem;
}}

#MainMenu, footer {{
    visibility: hidden;
}}

[data-testid="collapsedControl"] {{
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 0.85rem !important;
    left: 0.85rem !important;
    z-index: 999999 !important;
}}

[data-testid="collapsedControl"] button {{
    background: #111213 !important;
    border: 1px solid #26282b !important;
    border-radius: 6px !important;
    color: #f4f4f1 !important;
    box-shadow: 0 0 18px rgba(25,229,140,0.10) !important;
}}
[data-testid="stHeader"] {{ background: transparent; }}

h1, h2, h3, h4 {{
    color: {PALETTE["text"]};
    letter-spacing: 0;
}}

h2 {{
    font-size: 0.76rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase;
    color: {PALETTE["muted"]} !important;
    margin-top: 1.2rem !important;
}}

h3 {{
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    color: {PALETTE["text"]} !important;
}}

[data-testid="stSidebar"] {{
    background: #080909;
    border-right: 1px solid {PALETTE["border"]};
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] {{
    color: {PALETTE["muted"]};
}}

[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 1px solid {PALETTE["border"]};
    gap: 0;
}}

[data-testid="stTabs"] [role="tab"] {{
    color: {PALETTE["muted"]};
    background: transparent;
    border-bottom: 2px solid transparent;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    padding: 0.7rem 1.25rem;
}}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: {PALETTE["text"]};
    border-bottom-color: {PALETTE["green"]};
}}

div[data-baseweb="select"] > div {{
    background: {PALETTE["panel"]} !important;
    border: 1px solid {PALETTE["border"]} !important;
    border-radius: 6px !important;
}}

[data-testid="stDataFrame"] {{
    border: 1px solid {PALETTE["border"]};
    border-radius: 6px;
    overflow: hidden;
    font-family: 'IBM Plex Mono', monospace;
}}

.mi-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    border-bottom: 1px solid {PALETTE["border"]};
    padding: 0.4rem 0 1.1rem;
    margin-bottom: 1.25rem;
}}

.mi-kicker {{
    font-family: 'IBM Plex Mono', monospace;
    color: {PALETTE["green"]};
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    font-weight: 600;
}}

.mi-title {{
    color: {PALETTE["text"]};
    font-size: 2rem;
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: 0;
    margin-top: 0.25rem;
}}

.mi-subtitle {{
    color: {PALETTE["muted"]};
    font-size: 0.92rem;
    line-height: 1.55;
    max-width: 760px;
    margin-top: 0.55rem;
}}

.status-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    padding: 0.48rem 0.72rem;
    border: 1px solid rgba(25,229,140,0.34);
    border-radius: 999px;
    background: rgba(25,229,140,0.08);
    color: {PALETTE["green"]};
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.11em;
    text-transform: uppercase;
    white-space: nowrap;
}}

.header-status {{
    text-align: right;
    min-width: 230px;
}}

.pulse-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: {PALETTE["green"]};
    box-shadow: 0 0 12px {PALETTE["green"]};
}}

.metric-card {{
    border: 1px solid {PALETTE["border"]};
    border-radius: 8px;
    background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.018));
    padding: 1rem;
    min-height: 164px;
}}

.metric-card .label {{
    color: {PALETTE["muted"]};
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
}}

.metric-row {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.45rem;
}}

.score {{
    font-family: 'IBM Plex Mono', monospace;
    color: {PALETTE["text"]};
    font-size: 2rem;
    font-weight: 600;
    line-height: 1;
}}

.score.long {{
    font-size: 1.48rem;
    letter-spacing: 0;
}}

.delta {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    margin-top: 0.55rem;
}}

.delta.up {{ color: {PALETTE["green"]}; }}
.delta.down {{ color: {PALETTE["red"]}; }}
.delta.neutral {{ color: {PALETTE["yellow"]}; }}
.delta.placeholder {{ visibility: hidden; }}

.ring {{
    width: 66px;
    height: 66px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    box-shadow: 0 0 22px rgba(25,229,140,0.05);
}}

.ring-inner {{
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: #080909;
    color: {PALETTE["text"]};
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    font-size: 0.8rem;
}}

.panel {{
    border: 1px solid {PALETTE["border"]};
    border-radius: 8px;
    background: rgba(17,18,19,0.74);
    padding: 1rem;
}}

.panel-title {{
    color: {PALETTE["muted"]};
    font-size: 0.68rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.65rem;
}}

.insight-copy {{
    color: {PALETTE["text"]};
    font-size: 0.98rem;
    line-height: 1.65;
}}

.caption-mono {{
    color: {PALETTE["dim"]};
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.04em;
    margin-top: 0.7rem;
}}

.sidebar-brand {{
    border-bottom: 1px solid {PALETTE["border"]};
    padding-bottom: 1rem;
    margin-bottom: 1rem;
}}

.sidebar-mark {{
    color: {PALETTE["text"]};
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: 0.08em;
}}

.sidebar-copy {{
    color: {PALETTE["muted"]};
    font-size: 0.78rem;
    line-height: 1.6;
    margin-top: 0.5rem;
}}
</style>
"""


METRIC_LABELS = {
    "algorithm_group": "Algorithm Group",
    "algorithm_version": "Algorithm Version",
    "active_members": "Active Members",
    "active_members_30d": "Active Members 30D",
    "avg_app_minutes": "Average App Minutes",
    "avg_recovery": "Average Recovery",
    "avg_sleep_hours": "Average Sleep Hours",
    "avg_strain": "Average Strain",
    "low_engagement_pct": "Low Engagement Rate",
    "low_recovery_pct": "Low Recovery Rate",
    "model_type": "Model Type",
    "new_members_30d": "New Members 30D",
    "retention_rate_pct": "Retention Rate 30D",
    "row_count": "Rows",
    "subscription_continuity_pct": "Subscription Continuity 30D",
    "table_name": "Table",
}


def option_label(value: str) -> str:
    return value.replace("_", " ").title()


def metric_label(value: str) -> str:
    return METRIC_LABELS.get(value, option_label(value))


def experiment_variant_label(value: str) -> str:
    labels = {
        "control": "Baseline Algorithm",
        "treatment": "Release Candidate",
    }
    return labels.get(value, option_label(value))


def score_color(score: float) -> str:
    """Map a 0-100 score to recovery-style status colors."""
    if score >= 67:
        return PALETTE["green"]
    if score >= 34:
        return PALETTE["yellow"]
    return PALETTE["red"]


def delta_class(delta: float, inverse: bool = False) -> str:
    """Return the CSS class for a metric delta, optionally reversing polarity."""
    adjusted = -delta if inverse else delta
    if adjusted > 0:
        return "up"
    if adjusted < 0:
        return "down"
    return "neutral"


def format_delta(delta: float, suffix: str = "") -> str:
    return f"{delta:+.1f}{suffix}"


def metric_card(label: str, value: str, delta: Optional[float], ring_score: float, ring_label: str, color: str, suffix: str = "", inverse: bool = False) -> None:
    """Render a compact production-style metric card with a status ring."""
    score_percent = max(0, min(100, ring_score))
    score_class = "score long" if len(value) >= 6 else "score"
    delta_html = '<div class="delta placeholder">&nbsp;</div>'
    if delta is not None:
        delta_html = f'<div class="delta {delta_class(delta, inverse=inverse)}">{format_delta(delta, suffix)}</div>'
    st.markdown(
        f"""
<div class="metric-card">
  <div class="label">{label}</div>
  <div class="metric-row">
    <div>
      <div class="{score_class}">{value}</div>
      {delta_html}
    </div>
    <div class="ring" style="background: radial-gradient(circle at center, #080909 0 56%, transparent 57%), conic-gradient({color} {score_percent:.1f}%, #222629 0);">
      <div class="ring-inner">{ring_label}</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def style_chart(chart: alt.Chart, height: int = 300) -> alt.Chart:
    """Apply the app visual system to Altair charts."""
    return (
        chart.properties(height=height)
        .configure_view(strokeWidth=0)
        .configure_axis(
            gridColor=PALETTE["border"],
            domainColor=PALETTE["border"],
            tickColor=PALETTE["border"],
            labelColor=PALETTE["muted"],
            titleColor=PALETTE["muted"],
            labelFont="IBM Plex Mono",
            titleFont="Inter",
        )
        .configure_axisX(labelAngle=-35, labelLimit=150)
        .configure_axisY(labelAngle=0, labelLimit=170)
        .configure_legend(
            labelColor=PALETTE["muted"],
            titleColor=PALETTE["muted"],
            labelFont="Inter",
            titleFont="Inter",
        )
        .configure(background="transparent")
    )

"""Streamlit interface for the Member Insights Lakehouse application.

The app intentionally keeps business-facing member insights and data-platform
health in the same surface. That mirrors how production data products need to
serve both analytics consumers and the engineers responsible for metric trust.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "member_insights.duckdb"

# Visual language: dark, fitness analytics-inspired, and intentionally neutral.
# Recovery-style health metrics use green/yellow/red status semantics; other
# colors are restrained accents for sleep, strain, and platform telemetry.
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


def ensure_database() -> None:
    """Build the local warehouse on first run so the app is self-starting."""
    if DB_PATH.exists():
        return
    subprocess.run([sys.executable, str(ROOT / "generate_synthetic_data.py")], check=True, cwd=ROOT)


@st.cache_data
def query(sql: str) -> pd.DataFrame:
    """Run read-only analytical queries against the compiled DuckDB file."""
    ensure_database()
    with duckdb.connect(DB_PATH, read_only=True) as conn:
        return conn.execute(sql).df()


def quality_results() -> pd.DataFrame:
    """Expose the same quality gates used by the command-line test runner."""
    ensure_database()
    sys.path.insert(0, str(ROOT))
    from tests.run_quality_checks import run_checks

    return pd.DataFrame(run_checks(), columns=["check_name", "passed"])


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


def metric_card(label: str, value: str, delta: float, ring_score: float, ring_label: str, color: str, suffix: str = "", inverse: bool = False) -> None:
    """Render a compact production-style metric card with a status ring."""
    score_percent = max(0, min(100, ring_score))
    score_class = "score long" if len(value) >= 6 else "score"
    st.markdown(
        f"""
<div class="metric-card">
  <div class="label">{label}</div>
  <div class="metric-row">
    <div>
      <div class="{score_class}">{value}</div>
      <div class="delta {delta_class(delta, inverse=inverse)}">{format_delta(delta, suffix)}</div>
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
        .configure_legend(
            labelColor=PALETTE["muted"],
            titleColor=PALETTE["muted"],
            labelFont="Inter",
            titleFont="Inter",
        )
        .configure(background="transparent")
    )


def explain_metric(selected_cohort: str, latest: pd.Series, previous: pd.Series) -> str:
    """Create a deterministic stand-in for a governed AI insight.

    This deliberately avoids free-form SQL generation. In production, the same
    UX should call an approved LLM over curated aggregate tables and documented
    metric definitions.
    """
    recovery_delta = latest["avg_recovery"] - previous["avg_recovery"]
    sleep_delta = latest["avg_sleep_hours"] - previous["avg_sleep_hours"]
    strain_delta = latest["avg_strain"] - previous["avg_strain"]
    engagement_delta = latest["avg_app_minutes"] - previous["avg_app_minutes"]

    drivers = sorted(
        [
            ("sleep", abs(sleep_delta), f"sleep changed by {sleep_delta:+.2f} hours"),
            ("strain", abs(strain_delta), f"strain changed by {strain_delta:+.1f} points"),
            ("engagement", abs(engagement_delta), f"app engagement changed by {engagement_delta:+.1f} minutes"),
        ],
        key=lambda item: item[1],
        reverse=True,
    )

    direction = "improved" if recovery_delta >= 0 else "declined"
    return (
        f"For {selected_cohort.replace('_', ' ')}, average recovery {direction} by {recovery_delta:+.1f} points versus the prior day. "
        f"The strongest governed signals are {drivers[0][2]} and {drivers[1][2]}. "
        "In production, this would call an approved LLM over metric definitions and aggregate tables, not raw unrestricted member data."
    )


st.set_page_config(page_title="Member Insights", layout="wide", initial_sidebar_state="expanded")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        """
<div class="sidebar-brand">
  <div class="sidebar-mark">MEMBER INSIGHTS</div>
  <div class="sidebar-copy">
    Member insights lakehouse for recovery, sleep, strain, engagement, and platform-health analytics.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("## Cohort")

daily = query("select * from agg_cohort_daily order by event_date, cohort")
cohorts = sorted(daily["cohort"].unique())

with st.sidebar:
    selected_cohort = st.selectbox(
        "Member segment",
        cohorts,
        index=cohorts.index("athlete") if "athlete" in cohorts else 0,
        format_func=lambda value: value.replace("_", " ").title(),
    )
    st.markdown("## Stack")
    st.caption("Python · DuckDB · dbt-style SQL · Streamlit · quality checks")
    st.markdown("## Production Mirror")
    st.caption("Kafka/Spark · Snowflake · dbt · AWS · governed AI over metric marts")

filtered = daily[daily["cohort"] == selected_cohort].copy()
latest = filtered.iloc[-1]
previous = filtered.iloc[-2]

run_log = query("select * from pipeline_run_log")
checks = quality_results()
latest_run = run_log.iloc[-1]
quality_rate = checks["passed"].mean() * 100
latest_date = pd.to_datetime(filtered["event_date"].max()).strftime("%b %d, %Y")

st.markdown(
    f"""
<div class="mi-header">
  <div>
    <div class="mi-kicker">Member Insights Platform</div>
    <div class="mi-title">Performance Signals Command Center</div>
    <div class="mi-subtitle">
      Cohort-level recovery, sleep, strain, engagement, and data-platform health modeled from wearable and app events
      with trusted metrics, quality gates, observability, and governed AI explanations.
    </div>
  </div>
  <div class="header-status">
    <div class="status-pill"><span class="pulse-dot"></span><span>{latest_run["status"].upper()} · {quality_rate:.0f}% QUALITY</span></div>
    <div class="caption-mono">Latest member day · {latest_date}</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

tab_insights, tab_health, tab_dictionary = st.tabs(["Member Insights", "Data Platform Health", "Metric Dictionary"])

with tab_insights:
    recovery_delta = latest["avg_recovery"] - previous["avg_recovery"]
    sleep_delta = latest["avg_sleep_hours"] - previous["avg_sleep_hours"]
    strain_delta = latest["avg_strain"] - previous["avg_strain"]
    low_recovery_delta = latest["low_recovery_pct"] - previous["low_recovery_pct"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Recovery", f"{latest['avg_recovery']:.1f}%", recovery_delta, latest["avg_recovery"], "REC", score_color(latest["avg_recovery"]))
    with col2:
        sleep_score = min(100, latest["avg_sleep_hours"] / 8 * 100)
        metric_card("Sleep", f"{latest['avg_sleep_hours']:.2f}h", sleep_delta, sleep_score, "SLP", PALETTE["cyan"], suffix="h")
    with col3:
        strain_score = min(100, latest["avg_strain"] / 21 * 100)
        metric_card("Strain", f"{latest['avg_strain']:.1f}", strain_delta, strain_score, "STR", PALETTE["purple"])
    with col4:
        risk_score = 100 - latest["low_recovery_pct"]
        metric_card("Low Recovery Risk", f"{latest['low_recovery_pct']:.1f}%", low_recovery_delta, risk_score, "RISK", score_color(risk_score), suffix="%", inverse=True)

    st.markdown("## Cohort Trend")
    trend_base = filtered.melt(
        id_vars=["event_date"],
        value_vars=["avg_recovery", "avg_strain", "low_recovery_pct"],
        var_name="metric",
        value_name="value",
    )
    trend = (
        alt.Chart(trend_base)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("event_date:T", title="Date"),
            y=alt.Y("value:Q", title="Score"),
            color=alt.Color(
                "metric:N",
                scale=alt.Scale(
                    domain=["avg_recovery", "avg_strain", "low_recovery_pct"],
                    range=[PALETTE["green"], PALETTE["purple"], PALETTE["red"]],
                ),
                legend=alt.Legend(title=None),
            ),
            tooltip=["event_date:T", "metric:N", alt.Tooltip("value:Q", format=".1f")],
        )
    )
    st.altair_chart(style_chart(trend, height=330), use_container_width=True)

    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown("## Recovery vs. Strain")
        scatter = (
            alt.Chart(filtered)
            .mark_circle(size=110, opacity=0.88)
            .encode(
                x=alt.X("avg_strain:Q", title="Average Strain"),
                y=alt.Y("avg_recovery:Q", title="Average Recovery"),
                color=alt.Color(
                    "low_engagement_pct:Q",
                    scale=alt.Scale(range=[PALETTE["green"], PALETTE["yellow"], PALETTE["red"]]),
                    title="Low Engagement %",
                ),
                tooltip=[
                    "event_date:T",
                    alt.Tooltip("avg_recovery:Q", format=".1f"),
                    alt.Tooltip("avg_strain:Q", format=".1f"),
                    alt.Tooltip("low_engagement_pct:Q", format=".1f"),
                ],
            )
        )
        st.altair_chart(style_chart(scatter, height=320), use_container_width=True)
    with right:
        st.markdown(
            f"""
<div class="panel">
  <div class="panel-title">Governed AI Insight</div>
  <div class="insight-copy">{explain_metric(selected_cohort, latest, previous)}</div>
  <div class="caption-mono">Constrained to aggregate tables and metric definitions.</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.markdown(
            f"""
<div class="panel">
  <div class="panel-title">Current Segment</div>
  <div class="insight-copy">
    {selected_cohort.replace('_', ' ').title()} · {int(latest['active_members'])} active members ·
    {latest['avg_app_minutes']:.1f} avg app minutes · {latest['low_engagement_pct']:.1f}% low engagement.
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

with tab_health:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Pipeline", latest_run["status"].upper(), 0, quality_rate, "RUN", PALETTE["green"])
    with col2:
        metric_card("Raw Events", f"{latest_run['raw_events']:,}", 0, 100, "EVT", PALETTE["cyan"])
    with col3:
        metric_card("Member Days", f"{latest_run['member_days']:,}", 0, 100, "DAY", PALETTE["purple"])
    with col4:
        metric_card("Quality Pass Rate", f"{quality_rate:.0f}%", 0, quality_rate, "QA", PALETTE["green"])

    checks_display = checks.copy()
    checks_display["status"] = checks_display["passed"].map({True: "PASS", False: "FAIL"})
    st.markdown("## Quality Gates")
    st.dataframe(checks_display[["check_name", "status"]], use_container_width=True, hide_index=True)

    st.markdown("## Modeled Tables")
    table_counts = query(
        """
        select 'stg_member_events' as table_name, count(*) as row_count from stg_member_events
        union all select 'dim_members', count(*) from dim_members
        union all select 'fct_member_day', count(*) from fct_member_day
        union all select 'agg_cohort_daily', count(*) from agg_cohort_daily
        """
    )
    bars = (
        alt.Chart(table_counts)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("table_name:N", title=None, sort="-y"),
            y=alt.Y("row_count:Q", title="Rows"),
            color=alt.Color("table_name:N", legend=None, scale=alt.Scale(range=[PALETTE["green"], PALETTE["cyan"], PALETTE["purple"], PALETTE["yellow"]])),
            tooltip=["table_name:N", alt.Tooltip("row_count:Q", format=",")],
        )
    )
    st.altair_chart(style_chart(bars, height=320), use_container_width=True)

with tab_dictionary:
    dictionary = query("select * from metric_dictionary order by domain, metric_name")
    st.markdown("## Governed Metric Layer")
    st.dataframe(dictionary, use_container_width=True, hide_index=True)
    st.markdown(
        """
<div class="panel">
  <div class="panel-title">Production Mapping</div>
  <div class="insight-copy">
    Kafka or Kinesis for event intake, Spark for high-volume processing, Snowflake for warehouse serving,
    dbt for transformations/tests/docs, CloudWatch or Datadog for observability, and an approved LLM
    interface over curated metric marts.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

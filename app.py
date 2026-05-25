"""Streamlit interface for the Member Insights Lakehouse application.

The app intentionally keeps business-facing member insights and data-platform
health in the same surface. That mirrors how production data products need to
serve both analytics consumers and the engineers responsible for metric trust.
"""

from __future__ import annotations

import subprocess
import sys
import time
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


def option_label(value: str) -> str:
    return value.replace("_", " ").title()


def experiment_variant_label(value: str) -> str:
    labels = {
        "control": "Baseline Algorithm",
        "treatment": "Release Candidate",
    }
    return labels.get(value, option_label(value))


def filtered_member_days(member_days: pd.DataFrame, cohort: str, gender: str, plan: str) -> pd.DataFrame:
    df = member_days.copy()
    if cohort != "All":
        df = df[df["cohort"] == cohort]
    if gender != "All":
        df = df[df["gender"] == gender]
    if plan != "All":
        df = df[df["plan_type"] == plan]
    return df


def filtered_lifecycle(lifecycle: pd.DataFrame, cohort: str, gender: str, plan: str) -> pd.DataFrame:
    df = lifecycle.copy()
    if cohort != "All":
        df = df[df["cohort"] == cohort]
    if gender != "All":
        df = df[df["gender"] == gender]
    if plan != "All":
        df = df[df["plan_type"] == plan]
    return df


def daily_rollup(member_days: pd.DataFrame) -> pd.DataFrame:
    return (
        member_days.groupby("event_date", as_index=False)
        .agg(
            active_members=("member_id", "nunique"),
            avg_recovery=("recovery_score", "mean"),
            avg_sleep_hours=("sleep_minutes", lambda s: s.mean() / 60),
            avg_strain=("daily_strain", "mean"),
            avg_app_minutes=("app_session_minutes", "mean"),
            low_recovery_pct=("recovery_score", lambda s: (s < 45).mean() * 100),
            low_engagement_pct=("app_session_minutes", lambda s: (s < 2).mean() * 100),
        )
        .round(1)
        .sort_values("event_date")
    )


def lifecycle_summary(lifecycle: pd.DataFrame) -> dict[str, float]:
    total = int(lifecycle["total_members"].sum())
    active = int(lifecycle["active_members_30d"].sum())
    new = int(lifecycle["new_members_30d"].sum())
    churned = int(lifecycle["churned_members"].sum())
    continuity = active * 100 / total if total else 0
    retention_denominator = total - new
    retention = active * 100 / retention_denominator if retention_denominator else 0
    return {
        "total_members": total,
        "active_members_30d": active,
        "new_members_30d": new,
        "churned_members": churned,
        "subscription_continuity_pct": round(continuity, 1),
        "retention_rate_pct": round(min(retention, 100), 1),
    }


def assistant_answer(prompt: str, lifecycle: pd.DataFrame, member_days: pd.DataFrame) -> str:
    """Answer common member analytics questions from governed tables."""
    question = prompt.lower()
    summary = lifecycle_summary(lifecycle)
    latest_day = daily_rollup(member_days).iloc[-1]

    if "new" in question:
        by_channel = lifecycle.groupby("acquisition_channel", as_index=False)["new_members_30d"].sum().sort_values("new_members_30d", ascending=False)
        top = by_channel.iloc[0]
        return (
            f"There are {summary['new_members_30d']:,} new members in the last 30 days. "
            f"The strongest acquisition channel is {option_label(top['acquisition_channel'])} with {int(top['new_members_30d']):,} new members."
        )
    if "retention" in question:
        by_cohort = lifecycle.groupby("cohort", as_index=False).apply(lambda d: pd.Series({"retention_rate_pct": lifecycle_summary(d)["retention_rate_pct"]}))
        top = by_cohort.sort_values("retention_rate_pct", ascending=False).iloc[0]
        return f"Filtered retention is {summary['retention_rate_pct']:.1f}%. The strongest cohort is {option_label(top['cohort'])} at {top['retention_rate_pct']:.1f}%."
    if "subscription" in question or "continuity" in question:
        by_plan = lifecycle.groupby("plan_type", as_index=False).apply(lambda d: pd.Series({"subscription_continuity_pct": lifecycle_summary(d)["subscription_continuity_pct"]}))
        top = by_plan.sort_values("subscription_continuity_pct", ascending=False).iloc[0]
        return f"Subscription continuity is {summary['subscription_continuity_pct']:.1f}%. {option_label(top['plan_type'])} members have the strongest continuity at {top['subscription_continuity_pct']:.1f}%."
    if "gender" in question:
        by_gender = lifecycle.groupby("gender", as_index=False).apply(lambda d: pd.Series({"members": d["total_members"].sum(), "continuity": lifecycle_summary(d)["subscription_continuity_pct"]}))
        rows = "; ".join(f"{option_label(r.gender)}: {int(r.members):,} members, {r.continuity:.1f}% continuity" for r in by_gender.itertuples())
        return f"Gender breakdown for the current filters: {rows}."
    return (
        f"Current filtered population: {summary['total_members']:,} members, {summary['active_members_30d']:,} active in the last 30 days, "
        f"{summary['retention_rate_pct']:.1f}% retention, and {summary['subscription_continuity_pct']:.1f}% subscription continuity. "
        f"Latest performance signals show {latest_day.avg_recovery:.1f}% recovery, {latest_day.avg_sleep_hours:.1f}h sleep, and {latest_day.avg_strain:.1f} strain."
    )


def experiment_answer(prompt: str, experiment_summary: pd.DataFrame) -> str:
    summary = experiment_summary.iloc[0]
    return (
        f"{summary.experiment_name}: treatment improved recovery by {summary.recovery_lift:+.2f} points, "
        f"sleep by {summary.sleep_hours_lift:+.2f} hours, and app engagement by {summary.app_minutes_lift:+.2f} minutes. "
        f"Low-recovery rate changed by {summary.low_recovery_pct_delta:+.2f} percentage points, where negative is favorable."
    )


def llm_interpretation(prompt: str, grounded_answer: str, context: dict[str, object]) -> tuple[str, dict[str, object]]:
    """Optionally summarize grounded metrics with a local/OpenAI-compatible LLM."""
    from openai import OpenAI

    client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
    messages = [
        {
            "role": "system",
            "content": (
                "You are a concise analytics engineer. Use only the provided grounded answer and context. "
                "Do not invent numbers. Explain the business meaning in 2-3 sentences."
            ),
        },
        {
            "role": "user",
            "content": f"Question: {prompt}\nGrounded answer: {grounded_answer}\nContext: {context}",
        },
    ]
    started = time.perf_counter()
    response = client.chat.completions.create(model="llama3.2", messages=messages)
    latency = time.perf_counter() - started
    usage = getattr(response, "usage", None)
    metadata = {
        "provider": "local_ollama_openai_compatible_api",
        "model": "llama3.2",
        "latency_s": round(latency, 2),
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
        "estimated_cost_usd": 0.0,
    }
    return response.choices[0].message.content or grounded_answer, metadata


st.set_page_config(page_title="Member Insights", layout="wide", initial_sidebar_state="expanded")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

member_days = query("select * from fct_member_day")
lifecycle = query("select * from agg_member_lifecycle")
experiment_daily = query("select * from agg_experiment_daily")
experiment_summary = query("select * from agg_experiment_summary")
run_log = query("select * from pipeline_run_log")
checks = quality_results()
latest_run = run_log.iloc[-1]
quality_rate = checks["passed"].mean() * 100

cohorts = ["All"] + sorted(member_days["cohort"].unique())
genders = ["All"] + sorted(member_days["gender"].unique())
plans = ["All"] + sorted(member_days["plan_type"].unique())

with st.sidebar:
    st.markdown(
        """
<div class="sidebar-brand">
  <div class="sidebar-mark">MEMBER INSIGHTS</div>
  <div class="sidebar-copy">
    Growth, retention, subscription continuity, performance signals, and platform health for member analytics teams.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown("## Filters")
    selected_cohort = st.selectbox("Member segment", cohorts, index=0, format_func=option_label)
    selected_gender = st.selectbox("Gender", genders, format_func=option_label)
    selected_plan = st.selectbox("Plan", plans, format_func=option_label)
    st.markdown("## Stack")
    st.caption("Python · DuckDB · dbt-style SQL · Streamlit · quality checks")
    st.markdown("## Production Mirror")
    st.caption("Kafka/Spark · Snowflake · dbt · AWS · governed AI over metric marts")

filtered_days = filtered_member_days(member_days, selected_cohort, selected_gender, selected_plan)
filtered_life = filtered_lifecycle(lifecycle, selected_cohort, selected_gender, selected_plan)
filtered = daily_rollup(filtered_days)
latest = filtered.iloc[-1]
previous = filtered.iloc[-2]
lifecycle_kpis = lifecycle_summary(filtered_life)
latest_date = pd.to_datetime(filtered["event_date"].max()).strftime("%b %d, %Y")

st.markdown(
    f"""
<div class="mi-header">
  <div>
    <div class="mi-kicker">Member Insights Platform</div>
    <div class="mi-title">Performance Signals Command Center</div>
    <div class="mi-subtitle">
      Growth, retention, subscription continuity, recovery, sleep, strain, engagement, and data-platform health
      modeled from trusted member and event tables.
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

tab_growth, tab_signals, tab_experiment, tab_health, tab_dictionary, tab_assistant = st.tabs(
    ["Growth & Retention", "Performance Signals", "Experimentation", "Data Platform Health", "Metric Dictionary", "Insights Assistant"]
)

with tab_growth:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("New Members 30D", f"{lifecycle_kpis['new_members_30d']:,}", 0, min(100, lifecycle_kpis["new_members_30d"]), "NEW", PALETTE["cyan"])
    with col2:
        metric_card("Retention Rate", f"{lifecycle_kpis['retention_rate_pct']:.1f}%", 0, lifecycle_kpis["retention_rate_pct"], "RET", score_color(lifecycle_kpis["retention_rate_pct"]))
    with col3:
        metric_card("Subscription Continuity", f"{lifecycle_kpis['subscription_continuity_pct']:.1f}%", 0, lifecycle_kpis["subscription_continuity_pct"], "SUB", score_color(lifecycle_kpis["subscription_continuity_pct"]))
    with col4:
        metric_card("Active Members 30D", f"{lifecycle_kpis['active_members_30d']:,}", 0, 100, "ACT", PALETTE["green"])

    left, right = st.columns(2)
    with left:
        st.markdown("## Retention by Cohort")
        retention_by_cohort = filtered_life.groupby("cohort", as_index=False).apply(
            lambda d: pd.Series({"retention_rate_pct": lifecycle_summary(d)["retention_rate_pct"], "members": d["total_members"].sum()})
        )
        chart = alt.Chart(retention_by_cohort).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("cohort:N", title=None, sort="-y"),
            y=alt.Y("retention_rate_pct:Q", title="Retention %"),
            color=alt.Color("retention_rate_pct:Q", legend=None, scale=alt.Scale(range=[PALETTE["red"], PALETTE["yellow"], PALETTE["green"]])),
            tooltip=["cohort:N", alt.Tooltip("retention_rate_pct:Q", format=".1f"), alt.Tooltip("members:Q", format=",")],
        )
        st.altair_chart(style_chart(chart, height=310), use_container_width=True)
    with right:
        st.markdown("## New Members by Acquisition")
        acquisition = filtered_life.groupby("acquisition_channel", as_index=False)["new_members_30d"].sum()
        chart = alt.Chart(acquisition).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("acquisition_channel:N", title=None, sort="-y"),
            y=alt.Y("new_members_30d:Q", title="New Members"),
            color=alt.Color("acquisition_channel:N", legend=None, scale=alt.Scale(range=[PALETTE["green"], PALETTE["cyan"], PALETTE["purple"], PALETTE["yellow"], PALETTE["red"]])),
            tooltip=["acquisition_channel:N", alt.Tooltip("new_members_30d:Q", format=",")],
        )
        st.altair_chart(style_chart(chart, height=310), use_container_width=True)

    st.markdown("## Subscription Continuity by Plan and Gender")
    continuity = filtered_life.groupby(["plan_type", "gender"], as_index=False).apply(
        lambda d: pd.Series({"subscription_continuity_pct": lifecycle_summary(d)["subscription_continuity_pct"], "members": d["total_members"].sum()})
    )
    heatmap = alt.Chart(continuity).mark_rect(cornerRadius=3).encode(
        x=alt.X("plan_type:N", title="Plan"),
        y=alt.Y("gender:N", title="Gender"),
        color=alt.Color("subscription_continuity_pct:Q", title="Continuity %", scale=alt.Scale(range=[PALETTE["red"], PALETTE["yellow"], PALETTE["green"]])),
        tooltip=["plan_type:N", "gender:N", alt.Tooltip("subscription_continuity_pct:Q", format=".1f"), alt.Tooltip("members:Q", format=",")],
    )
    st.altair_chart(style_chart(heatmap, height=260), use_container_width=True)

with tab_signals:
    recovery_delta = latest["avg_recovery"] - previous["avg_recovery"]
    sleep_delta = latest["avg_sleep_hours"] - previous["avg_sleep_hours"]
    strain_delta = latest["avg_strain"] - previous["avg_strain"]
    low_recovery_delta = latest["low_recovery_pct"] - previous["low_recovery_pct"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Recovery", f"{latest['avg_recovery']:.1f}%", recovery_delta, latest["avg_recovery"], "REC", score_color(latest["avg_recovery"]))
    with col2:
        metric_card("Sleep", f"{latest['avg_sleep_hours']:.2f}h", sleep_delta, min(100, latest["avg_sleep_hours"] / 8 * 100), "SLP", PALETTE["cyan"], suffix="h")
    with col3:
        metric_card("Strain", f"{latest['avg_strain']:.1f}", strain_delta, min(100, latest["avg_strain"] / 21 * 100), "STR", PALETTE["purple"])
    with col4:
        risk_score = 100 - latest["low_recovery_pct"]
        metric_card("Low Recovery Risk", f"{latest['low_recovery_pct']:.1f}%", low_recovery_delta, risk_score, "RISK", score_color(risk_score), suffix="%", inverse=True)

    st.markdown("## Performance Trend")
    trend_base = filtered.melt(id_vars=["event_date"], value_vars=["avg_recovery", "avg_strain", "low_recovery_pct"], var_name="metric", value_name="value")
    trend = alt.Chart(trend_base).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("event_date:T", title="Date"),
        y=alt.Y("value:Q", title="Score"),
        color=alt.Color("metric:N", scale=alt.Scale(domain=["avg_recovery", "avg_strain", "low_recovery_pct"], range=[PALETTE["green"], PALETTE["purple"], PALETTE["red"]]), legend=alt.Legend(title=None)),
        tooltip=["event_date:T", "metric:N", alt.Tooltip("value:Q", format=".1f")],
    )
    st.altair_chart(style_chart(trend, height=330), use_container_width=True)

    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown("## Recovery vs. Strain")
        scatter = alt.Chart(filtered).mark_circle(size=110, opacity=0.88).encode(
            x=alt.X("avg_strain:Q", title="Average Strain"),
            y=alt.Y("avg_recovery:Q", title="Average Recovery"),
            color=alt.Color("low_engagement_pct:Q", scale=alt.Scale(range=[PALETTE["green"], PALETTE["yellow"], PALETTE["red"]]), title="Low Engagement %"),
            tooltip=["event_date:T", alt.Tooltip("avg_recovery:Q", format=".1f"), alt.Tooltip("avg_strain:Q", format=".1f"), alt.Tooltip("low_engagement_pct:Q", format=".1f")],
        )
        st.altair_chart(style_chart(scatter, height=320), use_container_width=True)
    with right:
        st.markdown(
            f"""
<div class="panel">
  <div class="panel-title">Governed AI Insight</div>
  <div class="insight-copy">{explain_metric(option_label(selected_cohort), latest, previous)}</div>
  <div class="caption-mono">Constrained to aggregate tables and metric definitions.</div>
</div>
""",
            unsafe_allow_html=True,
        )

with tab_experiment:
    summary = experiment_summary.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Recovery Lift", f"{summary['recovery_lift']:+.2f}", summary["recovery_lift"], min(100, 50 + summary["recovery_lift"] * 10), "REC", score_color(67 + summary["recovery_lift"]))
    with col2:
        metric_card("Sleep Lift", f"{summary['sleep_hours_lift']:+.2f}h", summary["sleep_hours_lift"], min(100, 50 + summary["sleep_hours_lift"] * 35), "SLP", PALETTE["cyan"], suffix="h")
    with col3:
        metric_card("Engagement Lift", f"{summary['app_minutes_lift']:+.2f}m", summary["app_minutes_lift"], min(100, 50 + summary["app_minutes_lift"] * 10), "APP", PALETTE["purple"], suffix="m")
    with col4:
        metric_card("Low Recovery Delta", f"{summary['low_recovery_pct_delta']:+.2f}pp", summary["low_recovery_pct_delta"], max(0, 70 - summary["low_recovery_pct_delta"] * 5), "GRD", score_color(70 - summary["low_recovery_pct_delta"]), suffix="pp", inverse=True)

    st.markdown("## Algorithm Version Comparison")
    metric_options = {
        "Recovery score": ("avg_recovery", "Average Recovery"),
        "Sleep hours": ("avg_sleep_hours", "Average Sleep Hours"),
        "App engagement minutes": ("avg_app_minutes", "Average App Minutes"),
        "Low recovery rate": ("low_recovery_pct", "Low Recovery %"),
    }
    selected_metric_label = st.radio(
        "Metric",
        options=list(metric_options.keys()),
        index=0,
        horizontal=True,
    )
    selected_metric, selected_axis = metric_options[selected_metric_label]
    experiment_trend = experiment_daily.copy()
    experiment_trend["variant_label"] = experiment_trend["experiment_variant"].map(experiment_variant_label)
    experiment_trend["metric_value"] = experiment_trend[selected_metric]
    trend = alt.Chart(experiment_trend).mark_line(point=True, strokeWidth=2.8).encode(
        x=alt.X("event_date:T", title="Date"),
        y=alt.Y("metric_value:Q", title=selected_axis, scale=alt.Scale(zero=False)),
        color=alt.Color(
            "variant_label:N",
            title="Algorithm Group",
            scale=alt.Scale(
                domain=["Baseline Algorithm", "Release Candidate"],
                range=[PALETTE["muted"], PALETTE["green"]],
            ),
        ),
        tooltip=[
            "event_date:T",
            "variant_label:N",
            "algorithm_version:N",
            alt.Tooltip("metric_value:Q", title=selected_axis, format=".2f"),
        ],
    )
    st.altair_chart(style_chart(trend, height=340), use_container_width=True)
    st.caption("Baseline Algorithm is the existing scoring logic. Release Candidate is the algorithm update being validated against outcome and guardrail metrics.")

    left, right = st.columns([1, 1])
    with left:
        st.markdown("## Variant Summary")
        variant_summary = (
            experiment_daily.groupby(["experiment_variant", "algorithm_version"], as_index=False)
            .agg(
                active_members=("active_members", "max"),
                avg_recovery=("avg_recovery", "mean"),
                avg_sleep_hours=("avg_sleep_hours", "mean"),
                avg_app_minutes=("avg_app_minutes", "mean"),
                low_recovery_pct=("low_recovery_pct", "mean"),
            )
            .round(2)
        )
        variant_summary["algorithm_group"] = variant_summary["experiment_variant"].map(experiment_variant_label)
        variant_summary = variant_summary[
            ["algorithm_group", "algorithm_version", "active_members", "avg_recovery", "avg_sleep_hours", "avg_app_minutes", "low_recovery_pct"]
        ]
        st.dataframe(variant_summary, use_container_width=True, hide_index=True)
    with right:
        st.markdown(
            f"""
<div class="panel">
  <div class="panel-title">Experiment Readout</div>
  <div class="insight-copy">{experiment_answer('summary', experiment_summary)}</div>
  <div class="caption-mono">Baseline = recovery_v1 · Release Candidate = recovery_v2 · Guardrail = low-recovery rate.</div>
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
        metric_card("Freshness", f"{latest_run['freshness_hours']:.1f}h", 0, max(0, 100 - latest_run["freshness_hours"]), "FR", PALETTE["green"])
    with col4:
        metric_card("Quality Pass Rate", f"{quality_rate:.0f}%", 0, quality_rate, "QA", PALETTE["green"])
    col5, col6 = st.columns(2)
    with col5:
        metric_card("Experiment Days", f"{latest_run['experiment_days']:,}", 0, 100, "EXP", PALETTE["purple"])
    with col6:
        metric_card("Modeled Tables", "10", 0, 100, "MDL", PALETTE["cyan"])

    checks_display = checks.copy()
    checks_display["status"] = checks_display["passed"].map({True: "PASS", False: "FAIL"})
    st.markdown("## Quality Gates")
    st.dataframe(checks_display[["check_name", "status"]], use_container_width=True, hide_index=True)

    st.markdown("## Modeled Tables")
    table_counts = query("select model_name as table_name, model_type, grain, row_count from model_inventory order by row_count desc")
    bars = alt.Chart(table_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("table_name:N", title=None, sort="-y"),
        y=alt.Y("row_count:Q", title="Rows"),
        color=alt.Color("model_type:N", legend=alt.Legend(title=None)),
        tooltip=["table_name:N", "model_type:N", "grain:N", alt.Tooltip("row_count:Q", format=",")],
    )
    st.altair_chart(style_chart(bars, height=320), use_container_width=True)
    st.dataframe(table_counts, use_container_width=True, hide_index=True)

with tab_dictionary:
    dictionary = query("select * from metric_dictionary order by domain, metric_name")
    st.markdown("## Governed Metric Layer")
    selected_domain = st.selectbox("Metric domain", ["All"] + sorted(dictionary["domain"].unique()))
    if selected_domain != "All":
        dictionary = dictionary[dictionary["domain"] == selected_domain]
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

with tab_assistant:
    st.markdown("## Governed Insights Assistant")
    st.caption("Answers are grounded in curated analytical functions over modeled tables. Optional local Ollama mode only interprets grounded results.")
    st.caption("Local LLM mode uses Ollama through an OpenAI-compatible local endpoint. It does not make paid OpenAI API calls.")
    use_llm = st.toggle("Use local Ollama interpretation", value=False, help="Runs against local Ollama through an OpenAI-compatible endpoint. No paid OpenAI API calls are made.")
    if use_llm:
        st.info("Local mode expects `ollama serve` and `ollama pull llama3.2`. Token usage is displayed when returned by the local server; estimated cost is $0.00.")
    suggestions = [
        "How many new members joined in the last 30 days?",
        "What is the retention rate?",
        "What is the subscription continuity by plan?",
        "Summarize the algorithm release experiment.",
        "Break down members by gender.",
        "Summarize the current member segment.",
    ]
    cols = st.columns(2)
    for idx, suggestion in enumerate(suggestions):
        if cols[idx % 2].button(suggestion, use_container_width=True):
            st.session_state["assistant_prompt"] = suggestion
    prompt = st.chat_input("Ask about member growth, retention, subscription continuity, or performance signals...")
    prompt = prompt or st.session_state.pop("assistant_prompt", None)
    if prompt:
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            grounded = experiment_answer(prompt, experiment_summary) if "experiment" in prompt.lower() or "algorithm" in prompt.lower() else assistant_answer(prompt, filtered_life, filtered_days)
            if use_llm:
                try:
                    answer, metadata = llm_interpretation(
                        prompt,
                        grounded,
                        {
                            "filters": {"cohort": selected_cohort, "gender": selected_gender, "plan": selected_plan},
                            "mode": "governed_metric_interpretation",
                        },
                    )
                    st.write(answer)
                    with st.expander("LLM usage", expanded=False):
                        st.json(metadata)
                except Exception as exc:
                    st.warning(f"Local LLM unavailable. Showing governed answer instead. Detail: {exc}")
                    st.write(grounded)
            else:
                st.write(grounded)

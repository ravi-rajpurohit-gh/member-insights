"""Streamlit interface for the Member Insights Lakehouse application."""

from __future__ import annotations

import html
from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st

from src.data import quality_results, query
from src.metrics import (
    daily_rollup,
    experiment_answer,
    explain_metric,
    filtered_lifecycle,
    filtered_member_days,
    governed_assistant_response,
    lifecycle_summary,
)
from src.ui import (
    CUSTOM_CSS,
    PALETTE,
    experiment_variant_label,
    metric_card,
    metric_label,
    option_label,
    score_color,
    style_chart,
)


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
    st.markdown(
        """
<div class="sidebar-footer">
  <span>Built by</span><br>
  <strong>Ravi Rajpurohit</strong><br>
  Data Engineering · Analytics Engineering · Governed AI
</div>
""",
        unsafe_allow_html=True,
    )

filtered_days = filtered_member_days(member_days, selected_cohort, selected_gender, selected_plan)
filtered_life = filtered_lifecycle(lifecycle, selected_cohort, selected_gender, selected_plan)
filtered = daily_rollup(filtered_days)
latest = filtered.iloc[-1]
previous = filtered.iloc[-2]
lifecycle_kpis = lifecycle_summary(filtered_life)
latest_date = pd.to_datetime(filtered["event_date"].max()).strftime("%b %d, %Y")


def render_assistant_message(role: str, content: str, mode: Optional[str] = None) -> None:
    """Render branded assistant messages without Streamlit's default chat avatars."""
    is_user = role == "user"
    css_role = "user" if is_user else "assistant"
    badge = "YOU" if is_user else "MI"
    role_label = "You" if is_user else "Member Insights Analyst"
    mode_label = mode or ("Question" if is_user else "Governed visual analysis")
    safe_content = html.escape(content).replace("\n", "<br>")
    st.markdown(
        f"""
<div class="assistant-message {css_role}">
  <div class="assistant-meta">
    <div class="assistant-badge">{badge}</div>
    <div>
      <div class="assistant-role">{role_label}</div>
      <div class="assistant-mode">{mode_label}</div>
    </div>
  </div>
  <div class="assistant-content">{safe_content}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def assistant_visual(selected_tool: str) -> Optional[alt.Chart]:
    """Return a governed visual for assistant routes that benefit from one."""
    if selected_tool == "summarize_growth":
        visual_data = filtered_life.groupby("acquisition_channel", as_index=False)["new_members_30d"].sum()
        visual_data["channel"] = visual_data["acquisition_channel"].map(option_label)
        return alt.Chart(visual_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("channel:N", title=None, sort="-y", axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("new_members_30d:Q", title="New Members 30D"),
            color=alt.Color("channel:N", legend=None, scale=alt.Scale(range=[PALETTE["green"], PALETTE["cyan"], PALETTE["purple"], PALETTE["yellow"], PALETTE["red"]])),
            tooltip=[
                alt.Tooltip("channel:N", title="Acquisition Channel"),
                alt.Tooltip("new_members_30d:Q", title="New Members 30D", format=","),
            ],
        )

    if selected_tool == "summarize_retention":
        visual_data = filtered_life.groupby("cohort", as_index=False).apply(
            lambda d: pd.Series({"retention_rate_pct": lifecycle_summary(d)["retention_rate_pct"]})
        )
        visual_data["member_segment"] = visual_data["cohort"].map(option_label)
        return alt.Chart(visual_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("member_segment:N", title=None, sort="-y", axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("retention_rate_pct:Q", title="Retention Rate 30D (%)"),
            color=alt.Color("retention_rate_pct:Q", legend=None, scale=alt.Scale(range=[PALETTE["red"], PALETTE["yellow"], PALETTE["green"]])),
            tooltip=[
                alt.Tooltip("member_segment:N", title="Member Segment"),
                alt.Tooltip("retention_rate_pct:Q", title="Retention Rate 30D", format=".1f"),
            ],
        )

    if selected_tool in {"summarize_subscription_continuity", "break_down_members_by_gender"}:
        visual_data = filtered_life.groupby(["plan_type", "gender"], as_index=False).apply(
            lambda d: pd.Series({"subscription_continuity_pct": lifecycle_summary(d)["subscription_continuity_pct"], "members": d["total_members"].sum()})
        )
        visual_data["plan"] = visual_data["plan_type"].map(option_label)
        visual_data["gender_label"] = visual_data["gender"].map(option_label)
        return alt.Chart(visual_data).mark_rect(cornerRadius=3).encode(
            x=alt.X("plan:N", title="Plan", axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("gender_label:N", title="Gender"),
            color=alt.Color("subscription_continuity_pct:Q", title="Continuity 30D (%)", scale=alt.Scale(range=[PALETTE["red"], PALETTE["yellow"], PALETTE["green"]])),
            tooltip=[
                alt.Tooltip("plan:N", title="Plan"),
                alt.Tooltip("gender_label:N", title="Gender"),
                alt.Tooltip("subscription_continuity_pct:Q", title="Subscription Continuity 30D", format=".1f"),
                alt.Tooltip("members:Q", title="Members", format=","),
            ],
        )

    if selected_tool in {"summarize_performance_signals", "summarize_member_segment"}:
        visual_data = filtered.melt(
            id_vars=["event_date"],
            value_vars=["avg_recovery", "avg_strain", "low_recovery_pct"],
            var_name="metric",
            value_name="value",
        )
        visual_data["metric_label"] = visual_data["metric"].map(metric_label)
        return alt.Chart(visual_data).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("event_date:T", title="Date"),
            y=alt.Y("value:Q", title="Score"),
            color=alt.Color("metric_label:N", title=None, scale=alt.Scale(range=[PALETTE["green"], PALETTE["purple"], PALETTE["red"]])),
            tooltip=[
                alt.Tooltip("event_date:T", title="Date"),
                alt.Tooltip("metric_label:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format=".1f"),
            ],
        )

    if selected_tool == "summarize_algorithm_experiment":
        summary_row = experiment_summary.iloc[0]
        visual_data = pd.DataFrame(
            [
                {"metric": "Recovery Lift", "value": summary_row["recovery_lift"], "unit": "points"},
                {"metric": "Sleep Lift", "value": summary_row["sleep_hours_lift"], "unit": "hours"},
                {"metric": "Engagement Lift", "value": summary_row["app_minutes_lift"], "unit": "minutes"},
                {"metric": "Low Recovery Delta", "value": summary_row["low_recovery_pct_delta"], "unit": "percentage points"},
            ]
        )
        return alt.Chart(visual_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("metric:N", title=None, sort=None, axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("value:Q", title="Lift / Delta"),
            color=alt.Color("value:Q", legend=None, scale=alt.Scale(range=[PALETTE["red"], PALETTE["yellow"], PALETTE["green"]])),
            tooltip=[
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("value:Q", title="Value", format="+.2f"),
                alt.Tooltip("unit:N", title="Unit"),
            ],
        )

    if selected_tool == "summarize_platform_health":
        visual_data = checks.copy()
        visual_data["status"] = visual_data["passed"].map({True: "Passed", False: "Failed"})
        visual_data["check_label"] = visual_data["check_name"].map(option_label)
        return alt.Chart(visual_data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("check_label:N", title=None, axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("count():Q", title="Checks"),
            color=alt.Color("status:N", title=None, scale=alt.Scale(domain=["Passed", "Failed"], range=[PALETTE["green"], PALETTE["red"]])),
            tooltip=[
                alt.Tooltip("check_label:N", title="Quality Check"),
                alt.Tooltip("status:N", title="Status"),
            ],
        )

    return None

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
        metric_card("New Members 30D", f"{lifecycle_kpis['new_members_30d']:,}", None, min(100, lifecycle_kpis["new_members_30d"]), "NEW", PALETTE["cyan"])
    with col2:
        metric_card("Retention Rate 30D", f"{lifecycle_kpis['retention_rate_pct']:.1f}%", None, lifecycle_kpis["retention_rate_pct"], "RET", score_color(lifecycle_kpis["retention_rate_pct"]))
    with col3:
        metric_card("Subscription Continuity 30D", f"{lifecycle_kpis['subscription_continuity_pct']:.1f}%", None, lifecycle_kpis["subscription_continuity_pct"], "SUB", score_color(lifecycle_kpis["subscription_continuity_pct"]))
    with col4:
        metric_card("Active Members 30D", f"{lifecycle_kpis['active_members_30d']:,}", None, 100, "ACT", PALETTE["green"])

    left, right = st.columns(2)
    with left:
        st.markdown("## Retention by Cohort")
        retention_by_cohort = filtered_life.groupby("cohort", as_index=False).apply(
            lambda d: pd.Series({"retention_rate_pct": lifecycle_summary(d)["retention_rate_pct"], "members": d["total_members"].sum()})
        )
        retention_by_cohort["member_segment"] = retention_by_cohort["cohort"].map(option_label)
        chart = alt.Chart(retention_by_cohort).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("member_segment:N", title=None, sort="-y", axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("retention_rate_pct:Q", title="Retention Rate 30D (%)"),
            color=alt.Color("retention_rate_pct:Q", legend=None, scale=alt.Scale(range=[PALETTE["red"], PALETTE["yellow"], PALETTE["green"]])),
            tooltip=[
                alt.Tooltip("member_segment:N", title="Member Segment"),
                alt.Tooltip("retention_rate_pct:Q", title="Retention Rate 30D", format=".1f"),
                alt.Tooltip("members:Q", title="Members", format=","),
            ],
        )
        st.altair_chart(style_chart(chart, height=310), use_container_width=True)
    with right:
        st.markdown("## New Members by Acquisition")
        acquisition = filtered_life.groupby("acquisition_channel", as_index=False)["new_members_30d"].sum()
        acquisition["acquisition_channel_label"] = acquisition["acquisition_channel"].map(option_label)
        chart = alt.Chart(acquisition).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("acquisition_channel_label:N", title=None, sort="-y", axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("new_members_30d:Q", title="New Members 30D"),
            color=alt.Color("acquisition_channel_label:N", legend=None, scale=alt.Scale(range=[PALETTE["green"], PALETTE["cyan"], PALETTE["purple"], PALETTE["yellow"], PALETTE["red"]])),
            tooltip=[
                alt.Tooltip("acquisition_channel_label:N", title="Acquisition Channel"),
                alt.Tooltip("new_members_30d:Q", title="New Members 30D", format=","),
            ],
        )
        st.altair_chart(style_chart(chart, height=310), use_container_width=True)

    continuity = filtered_life.groupby(["plan_type", "gender"], as_index=False).apply(
        lambda d: pd.Series({"subscription_continuity_pct": lifecycle_summary(d)["subscription_continuity_pct"], "members": d["total_members"].sum()})
    )
    continuity["plan"] = continuity["plan_type"].map(option_label)
    continuity["gender_label"] = continuity["gender"].map(option_label)
    continuity_best = continuity.sort_values("subscription_continuity_pct", ascending=False).iloc[0]
    continuity_watch = continuity.sort_values("subscription_continuity_pct", ascending=True).iloc[0]
    continuity_spread = continuity_best["subscription_continuity_pct"] - continuity_watch["subscription_continuity_pct"]
    continuity_insight = (
        f"{continuity_best['plan']} / {continuity_best['gender_label']} is the strongest visible segment at "
        f"{continuity_best['subscription_continuity_pct']:.1f}% subscription continuity over the last 30 days. "
        f"The widest segment spread is {continuity_spread:.1f} percentage points versus "
        f"{continuity_watch['plan']} / {continuity_watch['gender_label']}, which gives lifecycle and product teams "
        "a practical place to inspect onboarding, renewal, and engagement differences."
    )
    continuity_left, continuity_right = st.columns([1.2, 0.8])
    with continuity_left:
        st.markdown("## Subscription Continuity by Plan and Gender")
        heatmap = alt.Chart(continuity).mark_rect(cornerRadius=3).encode(
            x=alt.X("plan:N", title="Plan", axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("gender_label:N", title="Gender"),
            color=alt.Color("subscription_continuity_pct:Q", title="Continuity 30D (%)", scale=alt.Scale(range=[PALETTE["red"], PALETTE["yellow"], PALETTE["green"]])),
            tooltip=[
                alt.Tooltip("plan:N", title="Plan"),
                alt.Tooltip("gender_label:N", title="Gender"),
                alt.Tooltip("subscription_continuity_pct:Q", title="Subscription Continuity 30D", format=".1f"),
                alt.Tooltip("members:Q", title="Members", format=","),
            ],
        )
        st.altair_chart(style_chart(heatmap, height=275), use_container_width=True)
    with continuity_right:
        st.markdown(
            f"""
<div class="panel">
  <div class="panel-title">Governed AI Insight</div>
  <div class="insight-copy">{continuity_insight}</div>
  <div class="caption-mono">Derived from lifecycle aggregates and current filters.</div>
</div>
""",
            unsafe_allow_html=True,
        )

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
    trend_base["metric_label"] = trend_base["metric"].map(metric_label)
    trend = alt.Chart(trend_base).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X("event_date:T", title="Date"),
        y=alt.Y("value:Q", title="Score"),
        color=alt.Color("metric_label:N", scale=alt.Scale(domain=["Average Recovery", "Average Strain", "Low Recovery Rate"], range=[PALETTE["green"], PALETTE["purple"], PALETTE["red"]]), legend=alt.Legend(title=None)),
        tooltip=[
            alt.Tooltip("event_date:T", title="Date"),
            alt.Tooltip("metric_label:N", title="Metric"),
            alt.Tooltip("value:Q", title="Value", format=".1f"),
        ],
    )
    st.altair_chart(style_chart(trend, height=330), use_container_width=True)

    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown("## Recovery vs. Strain")
        scatter = alt.Chart(filtered).mark_circle(size=110, opacity=0.88).encode(
            x=alt.X("avg_strain:Q", title="Average Strain"),
            y=alt.Y("avg_recovery:Q", title="Average Recovery"),
            color=alt.Color("low_engagement_pct:Q", scale=alt.Scale(range=[PALETTE["green"], PALETTE["yellow"], PALETTE["red"]]), title="Low Engagement %"),
            tooltip=[
                alt.Tooltip("event_date:T", title="Date"),
                alt.Tooltip("avg_recovery:Q", title="Average Recovery", format=".1f"),
                alt.Tooltip("avg_strain:Q", title="Average Strain", format=".1f"),
                alt.Tooltip("low_engagement_pct:Q", title="Low Engagement Rate", format=".1f"),
            ],
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
            alt.Tooltip("event_date:T", title="Date"),
            alt.Tooltip("variant_label:N", title="Algorithm Group"),
            alt.Tooltip("algorithm_version:N", title="Algorithm Version"),
            alt.Tooltip("metric_value:Q", title=selected_axis, format=".2f"),
        ],
    )
    st.altair_chart(style_chart(trend, height=340), use_container_width=True)
    st.caption("Baseline Algorithm is the existing scoring logic. Release Candidate is the algorithm update being validated against outcome and guardrail metrics.")

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
    variant_summary = variant_summary.rename(columns={column: metric_label(column) for column in variant_summary.columns})
    st.dataframe(variant_summary, use_container_width=True, hide_index=True)

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
    health_cards = [
        ("Pipeline", latest_run["status"].upper(), quality_rate, "RUN", PALETTE["green"]),
        ("Raw Events", f"{latest_run['raw_events']:,}", 100, "EVT", PALETTE["cyan"]),
        ("Freshness", f"{latest_run['freshness_hours']:.1f}h", max(0, 100 - latest_run["freshness_hours"]), "FR", PALETTE["green"]),
        ("Quality Pass Rate", f"{quality_rate:.0f}%", quality_rate, "QA", PALETTE["green"]),
        ("Experiment Days", f"{latest_run['experiment_days']:,}", 100, "EXP", PALETTE["purple"]),
        ("Modeled Tables", "10", 100, "MDL", PALETTE["cyan"]),
    ]
    for row in (health_cards[:3], health_cards[3:]):
        cols = st.columns(3)
        for col, (label, value, ring_value, ring_text, ring_color) in zip(cols, row):
            with col:
                metric_card(label, value, None, ring_value, ring_text, ring_color)

    checks_display = checks.copy()
    checks_display["status"] = checks_display["passed"].map({True: "PASS", False: "FAIL"})
    st.markdown("## Quality Gates")
    st.dataframe(checks_display[["check_name", "status"]], use_container_width=True, hide_index=True)

    st.markdown("## Modeled Tables")
    table_counts = query("select model_name as table_name, model_type, grain, row_count from model_inventory order by row_count desc")
    table_counts["table_label"] = table_counts["table_name"].map(option_label)
    table_counts["model_type_label"] = table_counts["model_type"].map(option_label)
    bars = alt.Chart(table_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("table_label:N", title=None, sort="-y", axis=alt.Axis(labelAngle=-35)),
        y=alt.Y("row_count:Q", title="Rows"),
        color=alt.Color("model_type_label:N", legend=alt.Legend(title=None)),
        tooltip=[
            alt.Tooltip("table_label:N", title="Table"),
            alt.Tooltip("model_type_label:N", title="Model Type"),
            alt.Tooltip("grain:N", title="Grain"),
            alt.Tooltip("row_count:Q", title="Rows", format=","),
        ],
    )
    st.altair_chart(style_chart(bars, height=320), use_container_width=True)
    st.dataframe(
        table_counts[["table_label", "model_type_label", "grain", "row_count"]].rename(
            columns={"table_label": "Table", "model_type_label": "Model Type", "grain": "Grain", "row_count": "Rows"}
        ),
        use_container_width=True,
        hide_index=True,
    )

with tab_dictionary:
    dictionary = query("select * from metric_dictionary order by domain, metric_name")
    st.markdown("## Governed Metric Layer")
    selected_domain = st.selectbox("Metric domain", ["All"] + sorted(dictionary["domain"].unique()))
    if selected_domain != "All":
        dictionary = dictionary[dictionary["domain"] == selected_domain]
    dictionary_display = dictionary.copy()
    dictionary_display["metric_name"] = dictionary_display["metric_name"].map(metric_label)
    st.dataframe(
        dictionary_display.rename(
            columns={
                "metric_name": "Metric",
                "definition": "Definition",
                "source_logic": "Source Logic",
                "domain": "Domain",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
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
    st.caption("Ask natural-language questions. The analyst routes each question to governed functions, returns precise answers, and adds visuals when the question benefits from one.")
    suggestions = [
        "How many new members joined in the last 30 days?",
        "What is the retention rate?",
        "What is the subscription continuity by plan?",
        "Summarize the algorithm release experiment.",
        "Break down members by gender.",
        "Summarize the current member segment.",
    ]
    if "assistant_messages" not in st.session_state:
        st.session_state["assistant_messages"] = []

    cols = st.columns(2)
    for idx, suggestion in enumerate(suggestions):
        if cols[idx % 2].button(suggestion, use_container_width=True):
            st.session_state["assistant_prompt"] = suggestion

    if st.button("Clear assistant history", use_container_width=False):
        st.session_state["assistant_messages"] = []
        st.rerun()

    for message in st.session_state["assistant_messages"]:
        usage = message.get("usage")
        render_assistant_message(
            message["role"],
            message["content"],
            option_label(usage["mode"]) if usage and message["role"] == "assistant" else None,
        )
        if usage and message["role"] == "assistant":
            chart = assistant_visual(str(usage["selected_tool"]))
            if chart is not None:
                st.altair_chart(style_chart(chart, height=300), use_container_width=True)
            with st.expander("Analysis trace", expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tool", option_label(usage["selected_tool"]))
                c2.metric("Estimated tokens", f"{usage['total_tokens_estimated']:,}")
                c3.metric("Rows considered", f"{usage['rows_considered']:,}")
                c4.metric("Latency", f"{usage['latency_s']:.3f}s")
                c5, c6 = st.columns(2)
                c5.metric("API calls", f"{usage['api_calls']}")
                c6.metric("API cost", f"${usage['api_cost_usd']:.2f}")
                st.json(usage)

    prompt = st.chat_input("Ask about member growth, retention, subscription continuity, experiments, platform health, or metric definitions...")
    prompt = prompt or st.session_state.pop("assistant_prompt", None)
    if prompt:
        st.session_state["assistant_messages"].append({"role": "user", "content": prompt})
        render_assistant_message("user", prompt)
        answer, metadata = governed_assistant_response(
            prompt,
            filtered_life,
            filtered_days,
            experiment_summary,
            checks,
            latest_run,
            query("select * from metric_dictionary order by domain, metric_name"),
            {"member_segment": selected_cohort, "gender": selected_gender, "plan": selected_plan},
        )
        render_assistant_message("assistant", answer, option_label(metadata["mode"]))
        chart = assistant_visual(str(metadata["selected_tool"]))
        if chart is not None:
            st.altair_chart(style_chart(chart, height=300), use_container_width=True)
        with st.expander("Analysis trace", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tool", option_label(metadata["selected_tool"]))
            c2.metric("Estimated tokens", f"{metadata['total_tokens_estimated']:,}")
            c3.metric("Rows considered", f"{metadata['rows_considered']:,}")
            c4.metric("Latency", f"{metadata['latency_s']:.3f}s")
            c5, c6 = st.columns(2)
            c5.metric("API calls", f"{metadata['api_calls']}")
            c6.metric("API cost", f"${metadata['api_cost_usd']:.2f}")
            st.json(metadata)
        st.session_state["assistant_messages"].append({"role": "assistant", "content": answer, "usage": metadata})

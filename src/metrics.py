from __future__ import annotations

import time
from typing import Dict, Tuple

import pandas as pd

from .ui import metric_label, option_label


def explain_metric(selected_cohort: str, latest: pd.Series, previous: pd.Series) -> str:
    """Create a governed insight summary from aggregate movement."""
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


def estimate_tokens(text: str) -> int:
    """Approximate token count for a local, non-API assistant trace."""
    return max(1, round(len(text) / 4))


def experiment_answer(prompt: str, experiment_summary: pd.DataFrame) -> str:
    summary = experiment_summary.iloc[0]
    return (
        f"{summary.experiment_name}: treatment improved recovery by {summary.recovery_lift:+.2f} points, "
        f"sleep by {summary.sleep_hours_lift:+.2f} hours, and app engagement by {summary.app_minutes_lift:+.2f} minutes. "
        f"Low-recovery rate changed by {summary.low_recovery_pct_delta:+.2f} percentage points, where negative is favorable."
    )


def governed_assistant_response(
    prompt: str,
    lifecycle: pd.DataFrame,
    member_days: pd.DataFrame,
    experiment_summary: pd.DataFrame,
    checks: pd.DataFrame,
    latest_run: pd.Series,
    dictionary: pd.DataFrame,
    filters: Dict[str, str],
) -> Tuple[str, dict[str, object]]:
    """Route natural-language questions to governed analytical functions."""
    started = time.perf_counter()
    question = prompt.lower()
    summary = lifecycle_summary(lifecycle)
    rollup = daily_rollup(member_days)
    latest_day = rollup.iloc[-1]
    previous_day = rollup.iloc[-2] if len(rollup) > 1 else latest_day
    selected_tool = "summarize_member_segment"
    confidence = "medium"

    if any(word in question for word in ["experiment", "algorithm", "release", "variant", "baseline", "candidate", "a/b", "ab test"]):
        selected_tool = "summarize_algorithm_experiment"
        confidence = "high"
        answer = experiment_answer(prompt, experiment_summary)
        rows_considered = int(len(experiment_summary))
    elif any(word in question for word in ["pipeline", "platform", "health", "freshness", "quality", "checks", "models", "tables"]):
        selected_tool = "summarize_platform_health"
        confidence = "high"
        failed_checks = checks[~checks["passed"]]
        failed_text = "all quality gates are passing" if failed_checks.empty else f"{len(failed_checks)} quality gates need attention"
        answer = (
            f"The latest pipeline run is {latest_run['status']} with {latest_run['raw_events']:,} raw events, "
            f"{latest_run['freshness_hours']:.1f} hours of freshness lag, and {failed_text}. "
            f"The serving layer currently exposes {latest_run['experiment_days']:,} experiment-day rows and 10 modeled tables."
        )
        rows_considered = int(len(checks) + latest_run.get("raw_events", 0))
    elif any(word in question for word in ["dictionary", "definition", "metric means", "define"]):
        selected_tool = "lookup_metric_definition"
        confidence = "medium"
        matches = dictionary[
            dictionary.apply(
                lambda row: row.astype(str).str.lower().str.contains("|".join(question.split()), regex=True).any(),
                axis=1,
            )
        ]
        if matches.empty:
            matches = dictionary.head(5)
        definitions = "; ".join(f"{metric_label(row.metric_name)}: {row.definition}" for row in matches.head(4).itertuples())
        answer = f"Relevant governed metric definitions: {definitions}"
        rows_considered = int(len(dictionary))
    elif any(word in question for word in ["new", "growth", "joined", "signup", "acquisition", "channel"]):
        selected_tool = "summarize_growth"
        confidence = "high"
        by_channel = lifecycle.groupby("acquisition_channel", as_index=False)["new_members_30d"].sum().sort_values("new_members_30d", ascending=False)
        top = by_channel.iloc[0]
        answer = (
            f"There are {summary['new_members_30d']:,} new members in the last 30 days. "
            f"The strongest acquisition channel is {option_label(top['acquisition_channel'])} with {int(top['new_members_30d']):,} new members."
        )
        rows_considered = int(len(lifecycle))
    elif any(word in question for word in ["retention", "retained", "cohort"]):
        selected_tool = "summarize_retention"
        confidence = "high"
        by_cohort = lifecycle.groupby("cohort", as_index=False).apply(lambda d: pd.Series({"retention_rate_pct": lifecycle_summary(d)["retention_rate_pct"]}))
        top = by_cohort.sort_values("retention_rate_pct", ascending=False).iloc[0]
        answer = f"Filtered 30-day retention is {summary['retention_rate_pct']:.1f}%. The strongest cohort is {option_label(top['cohort'])} at {top['retention_rate_pct']:.1f}%."
        rows_considered = int(len(lifecycle))
    elif any(word in question for word in ["subscription", "continuity", "plan", "churn", "churned"]):
        selected_tool = "summarize_subscription_continuity"
        confidence = "high"
        by_plan = lifecycle.groupby("plan_type", as_index=False).apply(lambda d: pd.Series({"subscription_continuity_pct": lifecycle_summary(d)["subscription_continuity_pct"]}))
        top = by_plan.sort_values("subscription_continuity_pct", ascending=False).iloc[0]
        answer = f"30-day subscription continuity is {summary['subscription_continuity_pct']:.1f}%. {option_label(top['plan_type'])} members have the strongest continuity at {top['subscription_continuity_pct']:.1f}%."
        rows_considered = int(len(lifecycle))
    elif any(word in question for word in ["gender", "male", "female", "non binary", "not provided"]):
        selected_tool = "break_down_members_by_gender"
        confidence = "high"
        by_gender = lifecycle.groupby("gender", as_index=False).apply(lambda d: pd.Series({"members": d["total_members"].sum(), "continuity": lifecycle_summary(d)["subscription_continuity_pct"]}))
        rows = "; ".join(f"{option_label(r.gender)}: {int(r.members):,} members, {r.continuity:.1f}% continuity" for r in by_gender.itertuples())
        answer = f"Gender breakdown for the current filters: {rows}."
        rows_considered = int(len(lifecycle))
    elif any(word in question for word in ["recovery", "sleep", "strain", "performance", "engagement", "risk"]):
        selected_tool = "summarize_performance_signals"
        confidence = "high"
        answer = (
            f"Latest member-day signals show {latest_day.avg_recovery:.1f}% recovery, "
            f"{latest_day.avg_sleep_hours:.1f} hours of sleep, {latest_day.avg_strain:.1f} strain, "
            f"and {latest_day.low_recovery_pct:.1f}% low-recovery risk. Versus the prior day, recovery moved "
            f"{latest_day.avg_recovery - previous_day.avg_recovery:+.1f} points and sleep moved "
            f"{latest_day.avg_sleep_hours - previous_day.avg_sleep_hours:+.1f} hours."
        )
        rows_considered = int(len(member_days))
    else:
        answer = (
            f"Current filtered population: {summary['total_members']:,} members, {summary['active_members_30d']:,} active in the last 30 days, "
            f"{summary['retention_rate_pct']:.1f}% 30-day retention, and {summary['subscription_continuity_pct']:.1f}% 30-day subscription continuity. "
            f"Latest performance signals show {latest_day.avg_recovery:.1f}% recovery, {latest_day.avg_sleep_hours:.1f}h sleep, and {latest_day.avg_strain:.1f} strain."
        )
        rows_considered = int(len(lifecycle) + len(member_days))

    latency = time.perf_counter() - started
    prompt_tokens = estimate_tokens(prompt)
    completion_tokens = estimate_tokens(answer)
    metadata = {
        "mode": "governed_function_router",
        "selected_tool": selected_tool,
        "confidence": confidence,
        "api_calls": 0,
        "api_cost_usd": 0.0,
        "prompt_tokens_estimated": prompt_tokens,
        "completion_tokens_estimated": completion_tokens,
        "total_tokens_estimated": prompt_tokens + completion_tokens,
        "rows_considered": rows_considered,
        "latency_s": round(latency, 3),
        "filters": filters,
    }
    return answer, metadata

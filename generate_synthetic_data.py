from __future__ import annotations

"""Generate synthetic wearable member events and compile DuckDB models.

The generator creates realistic analytical shape, not real member data: member
cohorts, wearable signals, app engagement, workouts, and daily behavioral
variation. It then runs the SQL model build so the Streamlit app can read from a
single local warehouse artifact.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "member_insights.duckdb"
SQL_PATH = ROOT / "sql" / "01_build_models.sql"


@dataclass(frozen=True)
class ExperimentEffect:
    recovery_shift: float
    sleep_minutes_shift: int
    engagement_shift: float


EXPERIMENT_EFFECTS = {
    "control": ExperimentEffect(recovery_shift=0.0, sleep_minutes_shift=0, engagement_shift=0.0),
    "treatment": ExperimentEffect(recovery_shift=2.4, sleep_minutes_shift=11, engagement_shift=1.2),
}


def build_members(member_count: int, rng: np.random.Generator) -> pd.DataFrame:
    """Create synthetic member dimensions used for cohort analysis."""
    member_ids = [f"m_{idx:04d}" for idx in range(1, member_count + 1)]
    signup_start = pd.Timestamp.today().normalize() - pd.Timedelta(days=420)
    signup_offsets = rng.integers(0, 410, size=member_count)
    signup_dates = signup_start + pd.to_timedelta(signup_offsets, unit="D")
    plan_types = rng.choice(["monthly", "annual", "trial"], member_count, p=[0.38, 0.52, 0.10])
    cohorts = rng.choice(["new_member", "active_builder", "athlete", "health_optimizer"], member_count, p=[0.22, 0.34, 0.24, 0.20])
    churn_probability = np.where(plan_types == "annual", 0.08, np.where(plan_types == "monthly", 0.16, 0.34))
    churn_probability = churn_probability + np.where(cohorts == "athlete", -0.04, 0) + np.where(cohorts == "new_member", 0.06, 0)
    churned = rng.random(member_count) < np.clip(churn_probability, 0.03, 0.45)
    today = pd.Timestamp.today().normalize()
    cancellation_dates = []
    for signup_date, is_churned in zip(signup_dates, churned):
        if not is_churned:
            cancellation_dates.append(pd.NaT)
            continue
        earliest_cancel = signup_date + pd.Timedelta(days=31)
        latest_cancel = today - pd.Timedelta(days=5)
        if earliest_cancel >= latest_cancel:
            cancellation_dates.append(pd.NaT)
        else:
            cancel_offset = int(rng.integers(0, max(1, (latest_cancel - earliest_cancel).days)))
            cancellation_dates.append(earliest_cancel + pd.Timedelta(days=cancel_offset))

    return pd.DataFrame(
        {
            "member_id": member_ids,
            "cohort": cohorts,
            "plan_type": plan_types,
            "signup_date": signup_dates,
            "member_status": ["churned" if pd.notna(c) else "active" for c in cancellation_dates],
            "cancellation_date": cancellation_dates,
            "gender": rng.choice(["female", "male", "non_binary", "not_provided"], member_count, p=[0.42, 0.43, 0.04, 0.11]),
            "acquisition_channel": rng.choice(["organic", "paid_social", "referral", "retail_partner", "performance_event"], member_count, p=[0.30, 0.26, 0.18, 0.14, 0.12]),
            "primary_goal": rng.choice(["sleep", "fitness", "stress", "longevity"], member_count, p=[0.28, 0.34, 0.20, 0.18]),
            "age_band": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], member_count, p=[0.12, 0.38, 0.28, 0.15, 0.07]),
        }
    )


def build_experiment_assignments(members: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Assign active members to a synthetic algorithm-release experiment."""
    assignment_start = pd.Timestamp.today().normalize() - pd.Timedelta(days=38)
    eligible = members[members["member_status"] == "active"].copy()
    variants = rng.choice(["control", "treatment"], len(eligible), p=[0.5, 0.5])
    offsets = rng.integers(0, 8, len(eligible))

    return pd.DataFrame(
        {
            "experiment_id": "recovery_algorithm_release_q2",
            "experiment_name": "Recovery Algorithm Release Q2",
            "member_id": eligible["member_id"].to_list(),
            "variant": variants,
            "algorithm_version": ["recovery_v1" if v == "control" else "recovery_v2" for v in variants],
            "assigned_at": assignment_start + pd.to_timedelta(offsets, unit="D"),
            "rollout_channel": rng.choice(["feature_flag", "gradual_rollout", "internal_holdout"], len(eligible), p=[0.60, 0.32, 0.08]),
        }
    )


def build_events(members: pd.DataFrame, experiments: pd.DataFrame, days: int, rng: np.random.Generator) -> pd.DataFrame:
    """Create immutable wearable/app events for each member-day."""
    end_date = pd.Timestamp.today().normalize()
    dates = pd.date_range(end=end_date, periods=days, freq="D")
    rows: list[dict[str, object]] = []
    event_id = 1

    cohort_recovery_shift = {
        "new_member": -2,
        "active_builder": 2,
        "athlete": 5,
        "health_optimizer": 1,
    }
    experiment_lookup = {
        row.member_id: (pd.Timestamp(row.assigned_at), row.variant)
        for row in experiments.itertuples(index=False)
    }

    for member in members.itertuples(index=False):
        baseline_recovery = rng.normal(66, 10) + cohort_recovery_shift[member.cohort]
        baseline_hr = rng.normal(62, 8)
        engagement_bias = {"trial": -2.5, "monthly": 0.5, "annual": 2.0}[member.plan_type]

        for date in dates:
            if pd.notna(member.cancellation_date) and date > pd.Timestamp(member.cancellation_date):
                continue
            effect = EXPERIMENT_EFFECTS["control"]
            assigned_at, variant = experiment_lookup.get(member.member_id, (pd.NaT, "control"))
            if pd.notna(assigned_at) and date >= assigned_at:
                effect = EXPERIMENT_EFFECTS[variant]
            weekday_training = 1 if date.dayofweek in [0, 2, 4, 5] else 0
            strain = float(np.clip(rng.normal(9 + weekday_training * 2, 3), 1, 21))
            sleep_minutes = int(np.clip(rng.normal(435 - strain * 3 + effect.sleep_minutes_shift, 55), 240, 610))
            recovery = int(np.clip(baseline_recovery + effect.recovery_shift + (sleep_minutes - 420) / 10 - strain * 1.1 + rng.normal(0, 7), 8, 99))
            app_minutes = float(np.clip(rng.normal(8 + engagement_bias + effect.engagement_shift, 5), 0, 35))
            workout_minutes = int(np.clip(rng.normal(35 + weekday_training * 22, 24), 0, 150))

            event_specs = [
                ("heart_rate", baseline_hr + rng.normal(0, 5), None, None, None, 0, 0),
                ("sleep", baseline_hr - 7 + rng.normal(0, 3), None, sleep_minutes, recovery, 0, 0),
                ("recovery", baseline_hr + rng.normal(0, 4), strain, None, recovery, 0, 0),
                ("workout", baseline_hr + 32 + rng.normal(0, 12), strain, None, None, 0, workout_minutes),
                ("app_session", None, None, None, None, app_minutes, 0),
            ]

            if rng.random() < 0.08:
                event_specs.append(("journal", None, None, None, None, rng.uniform(1, 8), 0))

            for event_type, hr, event_strain, event_sleep, event_recovery, session_minutes, workout in event_specs:
                rows.append(
                    {
                        "event_id": f"evt_{event_id:07d}",
                        "member_id": member.member_id,
                        "event_ts": date + pd.to_timedelta(int(rng.integers(0, 86400)), unit="s"),
                        "event_type": event_type,
                        "heart_rate": None if hr is None else round(float(np.clip(hr, 38, 205)), 1),
                        "strain": event_strain,
                        "sleep_minutes": event_sleep,
                        "recovery_score": event_recovery,
                        "app_session_minutes": round(float(session_minutes), 1),
                        "workout_minutes": workout,
                    }
                )
                event_id += 1

    return pd.DataFrame(rows)


def build_warehouse() -> None:
    """Materialize SQL models into the local DuckDB warehouse."""
    with duckdb.connect(DB_PATH) as conn:
        conn.execute(SQL_PATH.read_text())


def main() -> None:
    """CLI entrypoint for regenerating data and rebuilding the warehouse."""
    parser = argparse.ArgumentParser(description="Generate synthetic wearable member events and DuckDB models.")
    parser.add_argument("--members", type=int, default=160)
    parser.add_argument("--days", type=int, default=45)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    rng = np.random.default_rng(args.seed)
    members = build_members(args.members, rng)
    experiments = build_experiment_assignments(members, rng)
    events = build_events(members, experiments, args.days, rng)

    members.to_csv(DATA_DIR / "members.csv", index=False)
    experiments.to_csv(DATA_DIR / "experiment_assignments.csv", index=False)
    events.to_csv(DATA_DIR / "member_events.csv", index=False)
    build_warehouse()

    print(f"Generated {len(members):,} members, {len(events):,} events, and {DB_PATH.name}.")


if __name__ == "__main__":
    main()

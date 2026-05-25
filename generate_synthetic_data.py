from __future__ import annotations

"""Generate synthetic wearable member events and compile DuckDB models.

The generator creates realistic analytical shape, not real member data: member
cohorts, wearable signals, app engagement, workouts, and daily behavioral
variation. It then runs the SQL model build so the Streamlit app can read from a
single local warehouse artifact.
"""

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "member_insights.duckdb"
SQL_PATH = ROOT / "sql" / "01_build_models.sql"


def build_members(member_count: int, rng: np.random.Generator) -> pd.DataFrame:
    """Create synthetic member dimensions used for cohort analysis."""
    member_ids = [f"m_{idx:04d}" for idx in range(1, member_count + 1)]
    signup_start = pd.Timestamp.today().normalize() - pd.Timedelta(days=420)
    signup_offsets = rng.integers(0, 330, size=member_count)

    return pd.DataFrame(
        {
            "member_id": member_ids,
            "cohort": rng.choice(["new_member", "active_builder", "athlete", "health_optimizer"], member_count, p=[0.22, 0.34, 0.24, 0.20]),
            "plan_type": rng.choice(["monthly", "annual", "trial"], member_count, p=[0.38, 0.52, 0.10]),
            "signup_date": signup_start + pd.to_timedelta(signup_offsets, unit="D"),
            "primary_goal": rng.choice(["sleep", "fitness", "stress", "longevity"], member_count, p=[0.28, 0.34, 0.20, 0.18]),
            "age_band": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], member_count, p=[0.12, 0.38, 0.28, 0.15, 0.07]),
        }
    )


def build_events(members: pd.DataFrame, days: int, rng: np.random.Generator) -> pd.DataFrame:
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

    for member in members.itertuples(index=False):
        baseline_recovery = rng.normal(66, 10) + cohort_recovery_shift[member.cohort]
        baseline_hr = rng.normal(62, 8)
        engagement_bias = {"trial": -2.5, "monthly": 0.5, "annual": 2.0}[member.plan_type]

        for date in dates:
            weekday_training = 1 if date.dayofweek in [0, 2, 4, 5] else 0
            strain = float(np.clip(rng.normal(9 + weekday_training * 2, 3), 1, 21))
            sleep_minutes = int(np.clip(rng.normal(435 - strain * 3, 55), 240, 610))
            recovery = int(np.clip(baseline_recovery + (sleep_minutes - 420) / 10 - strain * 1.1 + rng.normal(0, 7), 8, 99))
            app_minutes = float(np.clip(rng.normal(8 + engagement_bias, 5), 0, 35))
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
    events = build_events(members, args.days, rng)

    members.to_csv(DATA_DIR / "members.csv", index=False)
    events.to_csv(DATA_DIR / "member_events.csv", index=False)
    build_warehouse()

    print(f"Generated {len(members):,} members, {len(events):,} events, and {DB_PATH.name}.")


if __name__ == "__main__":
    main()

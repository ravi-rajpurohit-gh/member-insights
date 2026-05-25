from __future__ import annotations

"""Data quality checks for the Member Insights warehouse.

These checks are intentionally simple and inspectable. They represent the kinds
of gates that would become dbt tests, Great Expectations checks, or warehouse
assertions in a production data platform.
"""

from pathlib import Path

import duckdb


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "member_insights.duckdb"


CHECKS = [
    (
        "event_id_unique",
        "select count(*) = count(distinct event_id) from stg_member_events",
    ),
    (
        "member_id_not_null",
        "select count(*) = count(member_id) from stg_member_events",
    ),
    (
        "recovery_score_bounds",
        "select count(*) = 0 from stg_member_events where recovery_score is not null and (recovery_score < 0 or recovery_score > 100)",
    ),
    (
        "heart_rate_bounds",
        "select count(*) = 0 from stg_member_events where heart_rate is not null and (heart_rate < 35 or heart_rate > 220)",
    ),
    (
        "member_day_grain",
        "select count(*) = count(distinct member_id || '|' || cast(event_date as varchar)) from fct_member_day",
    ),
    (
        "freshness_recent",
        "select max(event_date) >= current_date - interval 2 day from stg_member_events",
    ),
]


def run_checks() -> list[tuple[str, bool]]:
    """Execute all quality checks and return `(check_name, passed)` tuples."""
    if not DB_PATH.exists():
        raise SystemExit("Database not found. Run `python generate_synthetic_data.py` first.")

    results: list[tuple[str, bool]] = []
    with duckdb.connect(DB_PATH, read_only=True) as conn:
        for name, sql in CHECKS:
            passed = bool(conn.execute(sql).fetchone()[0])
            results.append((name, passed))
    return results


def main() -> None:
    results = run_checks()
    for name, passed in results:
        print(f"{'PASS' if passed else 'FAIL'} {name}")
    if not all(passed for _, passed in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

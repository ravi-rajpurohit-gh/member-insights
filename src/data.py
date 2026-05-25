from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "member_insights.duckdb"


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

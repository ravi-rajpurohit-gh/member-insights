# Engineering Notes

Last updated: 2026-05-25

## Purpose

This project is a compact data product proof of concept: synthetic wearable and app events are transformed into member insights, platform health signals, and governed metric definitions.

It is intentionally small enough to explain in an interview, but the structure mirrors production habits:

- immutable event data,
- explicit table grains,
- dimensional and fact modeling,
- aggregate marts for dashboards,
- quality gates,
- metric documentation,
- and AI explanations constrained to trusted data products.

## Design Decisions

### Synthetic Data Only

The project uses generated data to avoid any implication of access to WHOOP private data. The generator focuses on analytical shape: cohorts, sleep, recovery, strain, app engagement, workouts, and member-day behavior.

### DuckDB as Local Warehouse

DuckDB keeps the proof of concept self-contained and fast to run locally. In production, the same modeling pattern maps to Snowflake with dbt managing transformations, tests, docs, and CI.

### dbt-Style SQL

The SQL build uses explicit staging, dimension, fact, aggregate, audit, and metric dictionary tables. This keeps the modeling easy to inspect and easy to discuss during system design.

### Governed AI Panel

The "AI-assisted insight" panel is deterministic by design. It summarizes metric movement from curated aggregates instead of generating arbitrary SQL over raw data. This shows the intended governance boundary for an LLM-powered analytics workflow.

### Product-Like UI

The Streamlit app uses a WHOOP-inspired visual language: dark surface, score rings, recovery/sleep/strain prominence, and green/yellow/red status semantics. It is inspired by public product patterns, not an official WHOOP interface.

## Production Mapping

| Local Demo | Production Equivalent |
| --- | --- |
| CSV event generation | Kafka/Kinesis event ingestion |
| DuckDB | Snowflake analytical warehouse |
| SQL model file | dbt model DAG |
| Python quality checks | dbt tests, Great Expectations, warehouse assertions |
| Streamlit dashboard | Internal analytics app, BI dashboard, or product analytics surface |
| Deterministic AI copy | Approved LLM over governed metric marts |

## Review Checklist

- Regenerate data: `python generate_synthetic_data.py`
- Run quality checks: `python tests/run_quality_checks.py`
- Run app: `streamlit run app.py`
- Confirm the dashboard tabs render: Member Insights, Data Platform Health, Metric Dictionary
- Confirm all quality checks pass before sharing or deploying

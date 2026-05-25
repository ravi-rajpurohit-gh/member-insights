# Engineering Notes

Last updated: 2026-05-25

## Purpose

This project is a compact data product proof of concept: synthetic wearable and app events are transformed into member insights, platform health signals, and governed metric definitions.

It is intentionally small enough to explain in an interview, but the structure mirrors production habits:

- immutable event data,
- explicit table grains,
- dimensional and fact modeling,
- aggregate marts for dashboards,
- lifecycle marts for member growth, retention, and subscription continuity,
- experimentation marts for algorithm-release control/treatment analysis,
- quality gates,
- metric documentation,
- and AI explanations constrained to trusted data products.

## Design Decisions

### Synthetic Data Only

The project uses generated data to avoid any implication of access to private company, product, or member data. The generator focuses on analytical shape: cohorts, sleep, recovery, strain, app engagement, workouts, and member-day behavior.

### DuckDB as Local Warehouse

DuckDB keeps the proof of concept self-contained and fast to run locally. In production, the same modeling pattern maps to Snowflake with dbt managing transformations, tests, docs, and CI.

### dbt-Style SQL

The SQL build uses explicit staging, dimension, fact, aggregate, audit, and metric dictionary tables. This keeps the modeling easy to inspect and easy to discuss during system design.

### Governed AI Panel

The "AI-assisted insight" panel is deterministic by design. It summarizes metric movement from curated aggregates instead of generating arbitrary SQL over raw data. This shows the intended governance boundary for an LLM-powered analytics workflow.

### Governed Insights Assistant

The assistant is function-backed rather than free-form. It answers common stakeholder questions using curated metrics and modeled tables, then displays an analysis trace with the selected analytical function, estimated tokens, rows considered, latency, and zero API cost. This avoids hosted API limits and local model setup while still demonstrating the production pattern: natural language routed to governed tools instead of arbitrary SQL or invented metrics.

LangChain is intentionally not included yet. The current assistant needs a small, inspectable tool boundary rather than a full orchestration framework. If the assistant grows to multiple retrieval sources, memory, evaluation traces, or provider routing, LangChain or LangGraph would become more useful.

### Experimentation & Algorithm Releases

The experiment mart models a recovery-algorithm release as a baseline/release-candidate comparison. Internally this follows standard control/treatment experimentation semantics, but the product UI uses more business-readable language. It tracks recovery lift, sleep lift, engagement lift, and low-recovery guardrail movement. This mirrors the kind of analytics internal product and data teams need when validating algorithm updates, feature flags, and phased rollouts.

### Product-Like UI

The Streamlit app uses a neutral health-and-performance analytics visual language: dark surface, score rings, recovery/sleep/strain prominence, and green/yellow/red status semantics.

### App Organization

The app currently uses one Streamlit page with six tabs. That is intentional for the interview use case: the hiring manager can understand the full data product in one surface without navigating across pages. The tabs map to natural stakeholder workflows: growth, performance, experimentation, platform health, metric governance, and natural-language analysis.

The implementation now keeps `app.py` focused on page flow and moves reusable logic into `src/` modules:

- `src/data.py` for DuckDB access and quality checks,
- `src/metrics.py` for governed calculations,
- `src/ui.py` for shared CSS, cards, labels, and charts.

A multi-page Streamlit structure would make sense if this becomes a larger portfolio product or a maintained internal tool. A practical future page structure would be `pages/1_Growth_Retention.py`, `pages/2_Performance_Signals.py`, `pages/3_Experimentation.py`, `pages/4_Platform_Health.py`, `pages/5_Metric_Dictionary.py`, and `pages/6_Insights_Assistant.py`. For now, the single-page tabbed app is the better demo shape because shared state, filters, styling, and chart conventions stay easy to follow.

## Production Mapping

| Local Demo | Production Equivalent |
| --- | --- |
| CSV event generation | Kafka/Kinesis event ingestion |
| DuckDB | Snowflake analytical warehouse |
| SQL model file | dbt model DAG |
| Python quality checks | dbt tests, Great Expectations, warehouse assertions |
| Streamlit dashboard | Internal analytics app, BI dashboard, or product analytics surface |
| Governed assistant router | Approved AI workflow over governed metric marts |
| Analysis trace | Token, latency, source, and tool telemetry |
| GitHub Actions workflow | Scheduled availability checks for hosted Streamlit apps |

## Review Checklist

- Regenerate data: `python generate_synthetic_data.py`
- Run quality checks: `python tests/run_quality_checks.py`
- Run app: `streamlit run app.py`
- Confirm the dashboard tabs render: Growth & Retention, Performance Signals, Experimentation, Data Platform Health, Metric Dictionary, Insights Assistant
- Confirm Insights Assistant answers from current modeled metrics
- Confirm assistant trace shows selected tool, estimated tokens, rows considered, latency, and zero API cost
- Confirm all quality checks pass before sharing or deploying

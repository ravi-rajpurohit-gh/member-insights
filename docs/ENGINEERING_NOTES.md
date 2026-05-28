# Engineering Notes

Last updated: 2026-05-27

## Purpose

This project is a compact data product reference implementation: generated wearable and app events are transformed into member insights, platform health signals, and governed metric definitions.

It is intentionally compact, but the structure mirrors production habits:

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

### Privacy-Safe Generated Data

The project uses generated data to avoid any implication of access to private company, product, or member data. The generator focuses on analytical shape: cohorts, sleep, recovery, strain, app engagement, workouts, and member-day behavior.

### DuckDB as Local Warehouse

DuckDB keeps the application self-contained and fast to run locally. In production, the same modeling pattern maps to Snowflake with dbt managing transformations, tests, docs, and CI.

### dbt-Style SQL

The SQL build uses explicit staging, dimension, fact, aggregate, audit, and metric dictionary tables. This keeps the modeling easy to inspect and easy to discuss during system design.

### Governed AI Panel

The "AI-assisted insight" panel is deterministic by design. It summarizes metric movement from curated aggregates instead of generating arbitrary SQL over raw data. This shows the intended governance boundary for an LLM-powered analytics workflow.

### Governed Insights Assistant

The assistant is function-backed rather than free-form. It answers common stakeholder questions using curated metrics and modeled tables, then displays an analysis trace with the selected analytical function, estimated tokens, rows considered, latency, and zero API cost. This avoids hosted API limits and local model setup while showing the production pattern: natural language routed to governed tools instead of arbitrary SQL or invented metrics.

The assistant now behaves as a governed visual analyst: the same routed answer can attach a contextual chart for growth, retention, subscription continuity, performance signals, experimentation, or platform health. This keeps the product experience close to modern AI analytics tools while preserving deterministic execution, explainable tool selection, and no dependency on paid API quotas.

The conversation UI uses native Streamlit bordered containers instead of custom chat-bubble HTML. User prompts are separated from analyst responses, assistant charts and trace metadata stay inside the response block, and prompt suggestions are hidden after the first turn. This keeps the assistant readable and reliable across local and hosted Streamlit environments.

LangChain is intentionally not included yet. The current assistant needs a small, inspectable tool boundary rather than a full orchestration framework. If the assistant grows to multiple retrieval sources, memory, evaluation traces, or provider routing, LangChain or LangGraph would become more useful.

### Experimentation & Algorithm Releases

The experiment mart models a recovery-algorithm release as a baseline/release-candidate comparison. Internally this follows standard control/treatment experimentation semantics, but the product UI uses more business-readable language. It tracks recovery lift, sleep lift, engagement lift, and low-recovery guardrail movement. This mirrors the kind of analytics internal product and data teams need when validating algorithm updates, feature flags, and phased rollouts.

### Product-Like UI

The Streamlit app uses a neutral health-and-performance analytics visual language: dark surface, score rings, recovery/sleep/strain prominence, and green/yellow/red status semantics.

The latest UI pass keeps attribution in the sidebar, gives governed insight/readout panels a consistent highlighted title treatment, and pairs dense visuals with a short business interpretation where it improves comprehension. Wide analytical tables stay full-width, while narrative readouts sit below them to avoid hiding columns.

### App Organization

The app currently uses one Streamlit page with six tabs. That is intentional for the product experience: users can understand the full data product in one surface without navigating across pages. The tabs map to natural stakeholder workflows: growth, performance, experimentation, platform health, metric governance, and natural-language analysis.

The implementation now keeps `app.py` focused on page flow and moves reusable logic into `src/` modules:

- `src/data.py` for DuckDB access and quality checks,
- `src/metrics.py` for governed calculations,
- `src/ui.py` for shared CSS, cards, labels, and charts.

A multi-page Streamlit structure would make sense if this becomes a larger portfolio product or a maintained internal tool. A practical future page structure would be `pages/1_Growth_Retention.py`, `pages/2_Performance_Signals.py`, `pages/3_Experimentation.py`, `pages/4_Platform_Health.py`, `pages/5_Metric_Dictionary.py`, and `pages/6_Insights_Assistant.py`. For now, the single-page tabbed app is the better product shape because shared state, filters, styling, and chart conventions stay easy to follow.

## Production Mapping

| Local Implementation | Production Equivalent |
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
- Confirm Insights Assistant can return a contextual chart for growth, retention, subscription continuity, performance, experimentation, and platform-health routes
- Confirm assistant trace shows selected tool, estimated tokens, rows considered, latency, API calls, and zero API cost
- Confirm all quality checks pass before sharing or deploying

## Checkpoint Record

2026-05-25 checkpoint:

- Public checkpoint: application, documentation, repository hygiene, and GitHub state are aligned.
- Python compile check passed with `PYTHONPYCACHEPREFIX=/private/tmp`.
- Quality checks passed with `python tests/run_quality_checks.py`.
- Browser smoke test confirmed the assistant renders a user prompt, analyst response, contextual chart, and analysis trace.
- Documentation updated in README, changelog, project tracker, engineering notes, and case study.
- Current recommendation: hold app structure stable and focus on walkthrough practice unless a bug or high-value polish item appears.

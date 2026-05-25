# Member Insights Lakehouse

A compact, production-minded analytics application for turning synthetic wearable and app events into trusted member insights. The project demonstrates how a data engineering team can model high-volume behavioral and physiological signals into reliable metrics for product analytics, experimentation, member insights, and AI-assisted workflows.

All data is synthetic. This project does not use or imply access to any private company, product, or member data.

## Vision

Modern health and performance products depend on more than raw events. Teams need durable data contracts, explainable metrics, quality controls, and fast ways for product, analytics, and ML partners to ask better questions about member behavior.

The vision for this project is a small but realistic member-insights platform:

- ingest wearable and app events as immutable facts,
- model those events into member-day and cohort-level analytical tables,
- enforce data quality before metrics reach dashboards,
- expose governed metric definitions,
- and use AI only on trusted aggregates and documented business logic.

The goal is to show that a proof of concept can be built quickly while still reflecting production-grade habits: clear table grains, validation, observability, metric governance, and privacy-aware AI boundaries.

## Who It Is Built For

This application is built for the kinds of teams that need to make member behavior understandable and actionable:

- **Data engineering teams** building reliable ELT pipelines, metric marts, and platform observability.
- **Analytics and product teams** measuring recovery, sleep, strain, engagement, cohort behavior, and experimentation outcomes.
- **Data science and ML partners** who need clean, documented, ML-ready member-day features.
- **Engineering managers and technical leads** evaluating whether a data platform can scale from prototype to production.

## What It Shows

The app has three views:

- **Member Insights:** cohort trends for recovery, sleep, strain, engagement, low-recovery risk, and a deterministic AI-style explanation of metric movement.
- **Data Platform Health:** pipeline status, table row counts, freshness, model outputs, and quality-check pass rate.
- **Metric Dictionary:** governed definitions and source logic for the metrics shown in the dashboard.

The underlying model covers common analytical table patterns:

- **Event table:** `stg_member_events`, immutable wearable and app events.
- **Dimension table:** `dim_members`, member cohort, plan, goal, and demographic attributes.
- **Fact table:** `fct_member_day`, one row per member per day for analytics and ML features.
- **Aggregate table:** `agg_cohort_daily`, cohort-level trusted metrics for dashboards and AI explanations.
- **Audit table:** `pipeline_run_log`, run status and modeled table counts.
- **Metric dictionary:** `metric_dictionary`, definitions and source logic for governed analytics.

## Why This Matters

Modern member-based health and performance products depend on scalable ELT, Python/PySpark, Snowflake-style warehousing, dbt-style modeling, Kafka/Spark-style event processing, reliability, observability, experimentation support, and data systems that power member insights. This project mirrors that problem shape in a runnable local environment:

- raw wearable/app signals become trusted member analytics,
- event data is transformed into clean member-day facts and cohort marts,
- quality checks protect downstream metrics,
- observability is treated as part of the data product,
- and AI is framed as a governed assistant over curated metrics, not a shortcut around data modeling.

This is intentionally compact, but the design choices reflect how the same system could evolve in a production data platform.

## Technology Stack

Built locally with:

- **Python:** synthetic data generation, orchestration script, and quality checks.
- **DuckDB:** local analytical warehouse for fast iteration.
- **SQL:** dbt-style transformations and table modeling.
- **Streamlit:** interactive dashboard and application surface.
- **Altair/Pandas:** visualizations and lightweight analytical processing.

Mirrors a production environment with:

- **Kafka or Kinesis:** wearable, app, journal, and product-event ingestion.
- **Spark/PySpark:** high-volume batch and streaming processing.
- **Snowflake:** analytical serving layer for product analytics, experimentation, and trusted metrics.
- **dbt:** model DAG, tests, documentation, metric contracts, and CI checks.
- **AWS:** S3 landing zones, Glue catalog, Lambda/Step Functions for lightweight workflows, and CloudWatch for logs and alerts.
- **Observability tooling:** freshness, schema drift, row-count anomalies, failed checks, and metric SLAs.
- **Approved LLM tooling:** natural-language explanations over curated aggregate tables and documented metric definitions.

## Architecture

```mermaid
flowchart LR
    A["Synthetic wearable and app events"] --> B["stg_member_events"]
    C["Synthetic member profiles"] --> D["dim_members"]
    B --> E["fct_member_day"]
    D --> E
    E --> F["agg_cohort_daily"]
    F --> G["Streamlit Member Insights"]
    F --> H["AI-assisted metric explanation"]
    I["Quality checks"] --> G
    J["metric_dictionary"] --> H
```

## Project Structure

```text
member-insights/
  app.py
  generate_synthetic_data.py
  requirements.txt
  docs/PROJECT_TRACKER.md
  sql/01_build_models.sql
  tests/run_quality_checks.py
  data/
```

Track goals, decisions, and progress in [docs/PROJECT_TRACKER.md](docs/PROJECT_TRACKER.md).

Engineering design notes live in [docs/ENGINEERING_NOTES.md](docs/ENGINEERING_NOTES.md), and release history is tracked in [CHANGELOG.md](CHANGELOG.md).

## Run Locally

```bash
pip install -r requirements.txt
python generate_synthetic_data.py
python tests/run_quality_checks.py
streamlit run app.py
```

## Quality Checks

The project includes checks for:

- duplicate event IDs,
- null member IDs,
- recovery score bounds,
- heart-rate bounds,
- one-row-per-member-per-day fact grain,
- and recent data freshness.

## 90-Second Walkthrough

1. "I built this as a small version of a member-insights platform: raw wearable and app events becoming reliable product analytics."
2. "The model starts with immutable event data, joins member dimensions, then creates a member-day fact table and cohort aggregate mart."
3. "The dashboard shows recovery, sleep, strain, engagement, and low-recovery risk by cohort, while the engineering tab shows freshness and quality checks."
4. "The AI explanation is deliberately governed. It explains metric movement from curated aggregates and definitions instead of querying raw member data freely."
5. "In production I would move this to Kafka/Spark/Snowflake/dbt, add orchestration and observability, and treat data quality as part of the product experience."

## What This Demonstrates About My Approach

- I can translate role and business context into a working proof of concept quickly.
- I model data around business questions, not just technical pipelines.
- I care about grain, quality, observability, documentation, and production migration paths.
- I use AI as an accelerator while preserving governance, explainability, and data boundaries.
- I can connect wearable telemetry, product analytics, and member-facing insights because I have worked on similar high-volume health-signal systems before.

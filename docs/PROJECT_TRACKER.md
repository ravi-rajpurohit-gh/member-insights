# WHOOP Member Insights Project Tracker

Last updated: 2026-05-25

## Goal

Prepare for the WHOOP Data Engineer II hiring manager conversation on 2026-05-29 with a compact, polished project that demonstrates member-insights analytics, wearable event modeling, data quality, observability, and AI-assisted metric explanation.

## Success Criteria

- Explain the project in 90 seconds without needing to run through every file.
- Show a working Streamlit dashboard if the hiring manager is interested.
- Connect the demo directly to WHOOP needs: member insights, analytics, Snowflake/dbt, Kafka/Spark, observability, and AI-assisted engineering.
- Use only synthetic data and be explicit that the project does not use WHOOP private data.

## Current Status

- Project scaffolded at `/Users/ravirajpurohit/Documents/Codex/2026-05-24/files-mentioned-by-the-user-data/whoop-member-insights`.
- Synthetic members and wearable/app events generated.
- DuckDB models created for event, dimension, member-day fact, cohort aggregate, pipeline audit, and metric dictionary tables.
- Streamlit app created with three tabs: Member Insights, Data Platform Health, Metric Dictionary.
- Quality checks added and passing.
- Browser verification completed at `http://localhost:8501`.

## Key Decisions

- Build a separate WHOOP-specific project instead of stretching `places-ops` across both interviews.
- Keep the project compact and polished rather than building heavy infrastructure.
- Use DuckDB and dbt-style SQL locally, with README production mapping to Snowflake, dbt, Kafka/Spark, AWS, and observability.
- Make the AI panel deterministic and governed, explaining aggregate metric changes rather than generating unrestricted SQL.

## Progress Log

| Date | Progress |
| --- | --- |
| 2026-05-24 | Created WHOOP Member Insights Lakehouse project with synthetic data generation, SQL models, quality checks, Streamlit app, and README walkthrough. |
| 2026-05-24 | Verified generated warehouse: 160 members, 36,589 events, 7,200 member-days, and 100% quality pass rate. |
| 2026-05-24 | Verified app in browser at `http://localhost:8501`. |
| 2026-05-25 | Rewrote README around project vision, target users, role alignment, production mapping, and production-grade proof-of-concept positioning. |
| 2026-05-25 | Redesigned Streamlit UI with a WHOOP-inspired dark performance dashboard, cohort filter sidebar, status pill, score-ring metric cards, governed AI panel, and production-style platform health view. |
| 2026-05-25 | Added code documentation, engineering notes, changelog, and README links in preparation for moving the project to active development and publishing to GitHub. |

## Open Questions

- Whether to deploy the Streamlit app publicly before the WHOOP call.
- Whether to add a short architecture image or keep the Mermaid diagram in README only.
- Whether to rehearse a live walkthrough or use the project only as supporting evidence if James asks.

## Next Actions

- Polish the 90-second walkthrough until it sounds conversational.
- Prepare answers for model design, event-table design, data quality, freshness, streaming vs batch, and AI governance.
- Optionally add screenshots to the README after the visual design is final.

## Interview Notes

- WHOOP call: 2026-05-29 at 10:30 AM.
- Hiring manager: James Glenister, Engineering Manager at WHOOP.
- Recruiter context: role involves member insights, analytics, and more.

## Storyline

Lead with: "I have already worked on the exact shape of problem WHOOP has: high-volume wearable telemetry, health signals, ML-ready datasets, and member-facing insights."

Anchor examples:

- KaHa Kafka pipeline processing 2B+ monthly wearable events.
- Sleep, stress, activity, HRV, PPG, and ECG signal processing.
- UTA wearable PPG/ECG research pipeline.
- A/B testing and self-serve analytics for product teams.
- AWS lakehouse, data quality, observability, and stakeholder dashboards.

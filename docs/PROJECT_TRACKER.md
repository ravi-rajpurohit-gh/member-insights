# Member Insights Lakehouse Project Tracker

Last updated: 2026-05-27

## Goal

Build a compact, production-minded member analytics platform that demonstrates event modeling, lifecycle analytics, experimentation, data quality, observability, metric governance, and governed AI-assisted analysis over trusted analytical tables.

## Success Criteria

- Explain the product vision and architecture in 90 seconds without walking through every file.
- Show a working Streamlit analytics surface with clear business workflows.
- Demonstrate how raw wearable, app, lifecycle, and experiment events become trusted member metrics.
- Show production habits: table grains, data quality gates, observability, metric definitions, and documented tradeoffs.
- Provide natural-language analytical access through governed functions, contextual visuals, and transparent trace metadata.
- Use only generated privacy-safe data and avoid any implication of private company, product, or member data access.

## Current Status

- Synthetic members and wearable/app events generated with lifecycle, acquisition, gender, plan, and status dimensions.
- DuckDB models created for event, dimension, member-day fact, cohort aggregate, lifecycle aggregate, pipeline audit, model inventory, and metric dictionary tables.
- Streamlit app now has six tabs: Growth & Retention, Performance Signals, Experimentation, Data Platform Health, Metric Dictionary, Insights Assistant.
- Quality checks are expanded and passing.
- GitHub repository pushed at `https://github.com/ravi-rajpurohit-gh/member-insights`.
- Insights Assistant now uses governed analytical routing with text responses, contextual charts, and trace metadata.
- Assistant UI uses bordered conversation blocks and hides prompt suggestions once a thread starts.
- Public checkpoint: application, documentation, repository hygiene, and GitHub state are aligned.
- Checkpoint status: app is stable, documented, tested, pushed, and ready for walkthrough practice.

## Key Decisions

- Build a separate member-insights platform instead of stretching `places-ops` across unrelated business domains.
- Keep the project compact and polished rather than building heavy infrastructure.
- Use DuckDB and dbt-style SQL locally, with README production mapping to Snowflake, dbt, Kafka/Spark, AWS, and observability.
- Make the AI panel deterministic and governed, explaining aggregate metric changes rather than generating unrestricted SQL.
- Replace local Ollama/hosted LLM dependency with a governed natural-language function router so the assistant works without API keys, local model setup, hosted API limits, or quota failures.
- Add governed visual responses to the assistant so natural-language answers can include charts without allowing arbitrary chart generation or hallucinated metric logic.
- Use Streamlit bordered containers for assistant messages instead of custom HTML chat bubbles, because native components render more reliably across themes and deployments.
- Hide assistant prompt suggestions after the first question so the conversation thread becomes the primary surface.
- Keep the application as a single Streamlit page with tabs for the current product surface. Multi-page Streamlit would be useful later if the app becomes a larger long-lived product, but the current single-page surface is faster to scan and easier to understand end to end.
- Extract shared helper code into `src/` modules before considering multi-page Streamlit, so filters, labels, CSS, and governed metrics remain consistent.

## Checkpoint Summary

| Area | Checkpoint State |
| --- | --- |
| Product surface | Six-tab internal analytics app with shared filters, production-style dark UI, metric cards, charts, dictionary, platform health, and governed assistant. |
| Data model | Generated privacy-safe raw events, members, experiment assignments, member-day facts, cohort aggregates, lifecycle aggregates, experiment marts, audit tables, model inventory, and metric dictionary. |
| Quality | 13 quality checks passing: identity, nulls, metric bounds, grain, freshness, accepted values, lifecycle bounds, model inventory, and experiment coverage. |
| AI/assistant | Governed function router with precise answers, contextual charts, selected tool, confidence, estimated tokens, rows considered, latency, API calls, and API cost. |
| UX | Chart labels, table headers, tooltips, KPI periods, assistant thread layout, insight panels, and sidebar attribution polished. |
| Code organization | `app.py` orchestrates the single-page product flow; `src/data.py`, `src/metrics.py`, and `src/ui.py` hold reusable data, metric, and UI logic. |
| Documentation | README, changelog, engineering notes, case study, and project tracker updated for portfolio-safe project framing. |

## Progress Log

| Date | Progress |
| --- | --- |
| 2026-05-24 | Created Member Insights Lakehouse project with generated privacy-safe data, SQL models, quality checks, Streamlit app, and README walkthrough. |
| 2026-05-24 | Verified generated warehouse: 160 members, 36,589 events, 7,200 member-days, and 100% quality pass rate. |
| 2026-05-24 | Verified app in browser at `http://localhost:8501`. |
| 2026-05-25 | Rewrote README around project vision, target users, production mapping, and production-minded implementation positioning. |
| 2026-05-25 | Redesigned Streamlit UI with a neutral dark performance dashboard, cohort filter sidebar, status pill, score-ring metric cards, governed AI panel, and production-style platform health view. |
| 2026-05-25 | Decided to keep public repository/project naming neutral as `member-insights` and avoid company-specific branding in public-facing files. |
| 2026-05-25 | Added code documentation, engineering notes, changelog, and README links in preparation for moving the project to active development and publishing to GitHub. |
| 2026-05-25 | Added GitHub Actions keep-alive workflow, lifecycle data model, Growth & Retention tab, richer Data Platform Health content, expanded Metric Dictionary, and a governed Insights Assistant. |
| 2026-05-25 | Added Experimentation tab for algorithm-release control/treatment analysis and optional local LLM interpretation over grounded assistant results. |
| 2026-05-25 | Replaced optional local LLM interpretation with a governed natural-language function router that answers from curated analytical functions and shows analysis trace metadata. |
| 2026-05-25 | Added analysis trace details: selected tool, estimated tokens, rows considered, latency, filters, confidence, zero API calls, and zero API cost. |
| 2026-05-25 | Removed `openai` dependency and eliminated local Ollama/runtime requirements from the app. |
| 2026-05-25 | Polished chart labels, table headers, tooltips, and metric names so the UI does not expose raw snake_case fields. |
| 2026-05-25 | Angled categorical chart labels for readability and clarified retention/subscription continuity KPIs as 30-day metrics. |
| 2026-05-25 | Removed decorative `+0.0` deltas from KPI cards without meaningful comparison periods. |
| 2026-05-25 | Verified syntax, quality checks, and browser smoke test after assistant and visualization polish. |
| 2026-05-25 | Refactored `app.py` from 1,147 lines to a focused single-page Streamlit flow backed by `src/data.py`, `src/metrics.py`, and `src/ui.py`. |
| 2026-05-25 | Removed stale assistant helpers and duplicate CSS while preserving the one-page tabbed product experience. |
| 2026-05-25 | Added portfolio case study documentation with lifecycle timeline, delivery phases, decision log, architecture, validation strategy, production evolution, and final state. |
| 2026-05-25 | Added governed visual analyst behavior: assistant answers can include contextual charts while preserving deterministic tool routing and zero external API dependency. |
| 2026-05-25 | Reworked assistant conversation UI into reliable bordered message blocks, removed `YOU`/`MI` custom badges, and hid prompt suggestions after the conversation starts. |
| 2026-05-25 | Completed project checkpoint: documentation, tracker, lifecycle, app state, quality checks, browser smoke test, git history, and GitHub push are aligned. |

## Open Questions

- Whether to deploy the Streamlit app publicly.
- Whether to add screenshots to README for GitHub polish.
- Whether to add a short architecture image or keep the Mermaid diagram in README only.
- Whether to split tabs into separate Streamlit pages later if the project grows beyond its current compact product scope.
- Whether to add an optional provider-backed LLM interpretation layer behind the governed router for environments where approved AI infrastructure exists.

## Next Actions

- Polish the 90-second product walkthrough until it sounds conversational.
- Prepare answers for model design, event-table design, data quality, freshness, streaming vs batch, experimentation, and AI governance.
- Optionally add screenshots to the README after the visual design is final.
- Keep app structure stable unless a bug is found.

## Walkthrough Notes

- Start with the product problem: teams need trusted member insights from event-heavy wearable and app data.
- Show the data path: generated raw events and member dimensions become member-day facts, lifecycle marts, cohort aggregates, experiment marts, and governed metrics.
- Show Growth & Retention for business value, Experimentation for product analytics, Data Platform Health for engineering trust, and Insights Assistant for governed AI access.
- Close with production mapping: Kafka/Kinesis, Spark, Snowflake, dbt, AWS observability, CI, and approved AI tooling.

## Storyline

Lead with: "This project models the shape of a modern member-insights platform: high-volume events, health and engagement signals, lifecycle analytics, experimentation, quality checks, observability, and governed AI access over trusted metrics."

Supporting themes:

- High-volume event processing and reliable analytical modeling.
- Health, performance, engagement, and lifecycle signal interpretation.
- Experimentation, self-serve analytics, and metric governance for product teams.
- Lakehouse-style architecture, data quality, observability, and stakeholder dashboards.

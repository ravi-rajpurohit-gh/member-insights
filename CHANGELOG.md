# Changelog

## 2026-05-25

- Upgraded the Insights Assistant into a governed visual analyst that can return text plus contextual charts.
- Replaced default Streamlit chat avatars with branded analyst/user message cards.
- Expanded assistant trace metadata with API call count and zero-cost display while preserving estimated token, row, and latency details.
- Enlarged the product identity label in the app header for stronger first-glance recognition.
- Added a governed insight panel beside subscription continuity so the heatmap has a clear business interpretation.
- Made insight/readout panel headers more visually prominent with a subtle animated highlight.
- Moved Experimentation readout below the variant summary so the full comparison table stays visible.
- Added sidebar attribution for Ravi Rajpurohit without interrupting the main analytics workspace.
- Added Experimentation tab for algorithm-release control/treatment analysis with recovery, sleep, engagement, and guardrail metrics.
- Improved experiment visualization with metric selector and baseline/release-candidate terminology.
- Added synthetic experiment assignment data and experiment marts.
- Reworked Insights Assistant into a governed natural-language function router with no hosted API, local model, or usage-limit dependency.
- Added analysis trace with selected tool, estimated tokens, rows considered, latency, and zero API cost.
- Polished chart labels, tooltips, and table headers so user-facing text no longer exposes raw snake_case field names.
- Updated categorical chart axes to angled labels for better readability.
- Clarified retention and subscription continuity KPI cards as 30-day metrics.
- Refactored Streamlit helper logic into `src/data.py`, `src/metrics.py`, and `src/ui.py` while keeping the app as a single-page tabbed product surface.
- Added portfolio-ready case study documentation with project lifecycle, delivery phases, decision log, architecture, validation strategy, and production evolution.
- Removed decorative zero deltas from KPI cards that do not have a meaningful comparison period.
- Added token/latency/cost metadata display for assistant responses.
- Added Growth & Retention analytics for new members, retention rate, subscription continuity, acquisition channels, gender, plan, and cohort filters.
- Added governed Insights Assistant powered by curated analytical functions instead of free-form SQL.
- Expanded Data Platform Health with freshness, lifecycle segments, model inventory, and additional data quality checks.
- Refined Data Platform Health KPI cards into a balanced grid and clamped synthetic same-day freshness at zero hours.
- Added GitHub Actions keep-alive workflow for Streamlit Community Cloud.
- Redesigned Streamlit UI with a neutral performance analytics dashboard.
- Added status-ring metric cards for recovery, sleep, strain, low-recovery risk, pipeline status, raw events, member days, and quality pass rate.
- Added custom Streamlit dark theme configuration.
- Rewrote README around vision, audience, business alignment, and production mapping.
- Added engineering notes for architecture, design decisions, and review workflow.
- Added project tracker for decisions, progress, and next actions.

## 2026-05-24

- Created synthetic member and wearable/app event generator.
- Added DuckDB SQL models for event, dimension, fact, aggregate, audit, and metric dictionary tables.
- Added data quality checks for IDs, bounds, grain, and freshness.
- Built initial Streamlit app with member insights, platform health, and metric dictionary tabs.

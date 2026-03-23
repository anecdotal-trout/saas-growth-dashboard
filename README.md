# SaaS Growth Metrics Dashboard

Tracks and calculates the core metrics a B2B SaaS company uses to measure growth: MRR, ARR, churn, net revenue retention, LTV/CAC, and unit economics — broken down by segment and over time.

## What it does

- Calculates MRR waterfall (new + expansion − churned)
- Tracks month-over-month growth and quarterly summaries
- Computes churn rates (gross revenue churn + logo churn)
- Estimates LTV and LTV/CAC ratio
- Breaks down performance by enterprise vs self-serve segments
- Runs an automated health check against industry benchmarks

## Quick start

```bash
pip install -r requirements.txt
python growth_dashboard.py
```

## Sample output

```
===========================================================================
CURRENT MONTH SNAPSHOT (Jun 2025)
===========================================================================

MRR:                    $ 3,488,000
ARR:                    $ 41,856,000
Total customers:        5,482
ARPU:                   $ 636
MoM MRR growth:         5.4%
Gross churn rate:       1.92%
Net revenue retention:  101.8%
LTV/CAC ratio:          31.9x
Trial conversion rate:  24.7%
```

## Metrics explained

| Metric | Formula | Why it matters |
|--------|---------|----------------|
| **MRR** | Sum of all monthly recurring revenue | Core health indicator |
| **Net New MRR** | New + Expansion − Churned | Shows if growth is accelerating |
| **Gross Churn Rate** | Churned MRR / Prior Month MRR | Revenue lost from existing customers |
| **Net Revenue Retention** | (Prior MRR − Churn + Expansion) / Prior MRR | >100% means existing customers grow over time |
| **LTV** | ARPU × Gross Margin / Monthly Churn Rate | Lifetime value of a customer |
| **LTV/CAC** | LTV / Cost to Acquire | Unit economics — should be >3x |

## How it works

1. **Data load**: Reads 18 months of monthly SaaS metrics from CSV into SQLite
2. **Derived metrics**: Calculates MoM growth rates, churn rates, NRR, LTV, and LTV/CAC in pandas
3. **SQL aggregation**: Runs quarterly rollups and segment breakdowns via SQLite
4. **Health check**: Compares current metrics against standard B2B SaaS benchmarks and flags areas of strength/concern

## Data

`/data/monthly_metrics.csv` contains 18 months of simulated but realistic SaaS metrics including:

- Customer counts (total, new, churned) and MRR components
- Trial funnel (starts, conversions)
- Segment split (enterprise vs self-serve with separate MRR and customer counts)

## Tech

- **Python** — pandas for time-series calculations and derived metrics
- **SQL** (SQLite) — quarterly aggregations and segment analysis
- **No external dependencies** beyond pandas

## Context

This is the kind of model that typically lives in a Google Sheet but breaks as soon as the data gets complex or someone accidentally deletes a formula. Building it in Python makes it reproducible, testable, and version-controlled — which is the point. If you can build this, you can maintain the real thing.

## Other projects

- [b2b-pipeline-analyzer](https://github.com/anecdotal-trout/b2b-pipeline-analyzer) — Marketing spend → pipeline ROI analysis
- [influencer-marketing-report](https://github.com/anecdotal-trout/influencer-marketing-report) — Influencer campaign ROI analysis

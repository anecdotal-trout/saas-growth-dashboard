"""
SaaS Growth Metrics Dashboard
==============================
Calculates and tracks the core metrics a B2B SaaS company uses to measure
growth health: MRR, churn, net revenue retention, LTV, CAC ratio, and
unit economics by segment.

Designed to replicate the kind of spreadsheet model a growth or finance
team maintains — but in code, so it's version-controlled and reproducible.
"""

import sqlite3
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Assumed values for unit economics (would come from finance team in practice)
BLENDED_CAC = 850          # average cost to acquire a customer
AVG_GROSS_MARGIN = 0.82    # typical for SaaS
MONTHS_IN_YEAR = 12


def load_data():
    """Load monthly metrics into pandas and SQLite."""
    df = pd.read_csv(os.path.join(DATA_DIR, "monthly_metrics.csv"))
    conn = sqlite3.connect(":memory:")
    df.to_sql("metrics", conn, if_exists="replace", index=False)
    return conn, df


# ---------------------------------------------------------------------------
# CALCULATED METRICS
# ---------------------------------------------------------------------------

def calculate_growth_metrics(df):
    """Add derived columns for MoM growth, churn rates, NRR, etc."""
    df = df.copy()

    # MRR growth
    df["mrr_mom_growth_pct"] = df["mrr_usd"].pct_change() * 100
    df["net_new_mrr"] = df["new_mrr_usd"] - df["churned_mrr_usd"] + df["expansion_mrr_usd"]

    # Churn metrics (using prior month's base)
    df["gross_churn_rate_pct"] = (
        df["churned_mrr_usd"] / df["mrr_usd"].shift(1) * 100
    )
    df["net_revenue_retention_pct"] = (
        (df["mrr_usd"].shift(1) - df["churned_mrr_usd"] + df["expansion_mrr_usd"])
        / df["mrr_usd"].shift(1) * 100
    )

    # Logo churn
    df["logo_churn_rate_pct"] = (
        df["churned_customers"] / df["total_customers"].shift(1) * 100
    )

    # Trial conversion rate
    df["trial_conversion_pct"] = (
        df["trial_conversions"] / df["trial_starts"] * 100
    )

    # LTV estimate (simple: ARPU * gross margin / monthly churn rate)
    monthly_churn_decimal = df["gross_churn_rate_pct"] / 100
    df["estimated_ltv"] = (
        df["arpu_usd"] * AVG_GROSS_MARGIN / monthly_churn_decimal.replace(0, pd.NA)
    )
    df["ltv_cac_ratio"] = df["estimated_ltv"] / BLENDED_CAC

    # ARR
    df["arr_usd"] = df["mrr_usd"] * MONTHS_IN_YEAR

    return df.round(2)


# ---------------------------------------------------------------------------
# SQL QUERIES
# ---------------------------------------------------------------------------

SEGMENT_MIX_SQL = """
    SELECT
        month,
        enterprise_customers,
        self_serve_customers,
        ROUND(enterprise_mrr_usd * 100.0 / mrr_usd, 1)     AS enterprise_mrr_share_pct,
        ROUND(self_serve_mrr_usd * 100.0 / mrr_usd, 1)     AS self_serve_mrr_share_pct,
        ROUND(enterprise_mrr_usd * 1.0
              / NULLIF(enterprise_customers, 0), 0)          AS enterprise_arpu,
        ROUND(self_serve_mrr_usd * 1.0
              / NULLIF(self_serve_customers, 0), 0)          AS self_serve_arpu
    FROM metrics
    ORDER BY month
"""

QUARTERLY_SUMMARY_SQL = """
    SELECT
        CASE
            WHEN CAST(SUBSTR(month, 6, 2) AS INTEGER) BETWEEN 1 AND 3
                THEN SUBSTR(month, 1, 4) || '-Q1'
            WHEN CAST(SUBSTR(month, 6, 2) AS INTEGER) BETWEEN 4 AND 6
                THEN SUBSTR(month, 1, 4) || '-Q2'
            WHEN CAST(SUBSTR(month, 6, 2) AS INTEGER) BETWEEN 7 AND 9
                THEN SUBSTR(month, 1, 4) || '-Q3'
            ELSE SUBSTR(month, 1, 4) || '-Q4'
        END                                                   AS quarter,
        SUM(new_customers)                                    AS new_customers,
        SUM(churned_customers)                                AS churned,
        SUM(new_mrr_usd)                                      AS new_mrr,
        SUM(churned_mrr_usd)                                  AS lost_mrr,
        SUM(expansion_mrr_usd)                                AS expansion_mrr,
        ROUND(SUM(new_mrr_usd) - SUM(churned_mrr_usd)
              + SUM(expansion_mrr_usd), 0)                    AS net_new_mrr
    FROM metrics
    GROUP BY quarter
    ORDER BY quarter
"""


# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------

def print_section(title):
    print(f"\n{'='*75}")
    print(f"  {title}")
    print(f"{'='*75}")


def main():
    conn, raw_df = load_data()
    df = calculate_growth_metrics(raw_df)

    print("\n" + "="*75)
    print("  SAAS GROWTH METRICS DASHBOARD")
    print("  Period: Jan 2024 – Jun 2025")
    print("="*75)

    # --- Current Snapshot ---
    print_section("CURRENT MONTH SNAPSHOT (Jun 2025)")
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    print(f"  MRR:                     ${latest['mrr_usd']:>12,.0f}")
    print(f"  ARR:                     ${latest['arr_usd']:>12,.0f}")
    print(f"  Total customers:         {latest['total_customers']:>12,.0f}")
    print(f"  ARPU:                    ${latest['arpu_usd']:>12,.0f}")
    print(f"  MoM MRR growth:          {latest['mrr_mom_growth_pct']:>11.1f}%")
    print(f"  Gross churn rate:        {latest['gross_churn_rate_pct']:>11.2f}%")
    print(f"  Net revenue retention:   {latest['net_revenue_retention_pct']:>11.1f}%")
    print(f"  LTV/CAC ratio:           {latest['ltv_cac_ratio']:>11.1f}x")
    print(f"  Trial conversion rate:   {latest['trial_conversion_pct']:>11.1f}%")

    # --- Monthly Trend (key metrics) ---
    print_section("MONTHLY TREND — KEY METRICS")
    trend_cols = [
        "month", "mrr_usd", "mrr_mom_growth_pct", "net_new_mrr",
        "gross_churn_rate_pct", "net_revenue_retention_pct",
        "ltv_cac_ratio", "total_customers"
    ]
    print(df[trend_cols].to_string(index=False))

    # --- MRR Waterfall (latest 6 months) ---
    print_section("MRR WATERFALL — LAST 6 MONTHS")
    waterfall_cols = ["month", "mrr_usd", "new_mrr_usd", "expansion_mrr_usd",
                      "churned_mrr_usd", "net_new_mrr"]
    print(df[waterfall_cols].tail(6).to_string(index=False))

    # --- Quarterly Summary ---
    print_section("QUARTERLY SUMMARY")
    quarterly_df = pd.read_sql(QUARTERLY_SUMMARY_SQL, conn)
    print(quarterly_df.to_string(index=False))

    # --- Segment Mix ---
    print_section("SEGMENT MIX — ENTERPRISE vs SELF-SERVE")
    segment_df = pd.read_sql(SEGMENT_MIX_SQL, conn)
    print(segment_df.to_string(index=False))

    # --- Health Check ---
    print_section("GROWTH HEALTH CHECK")
    checks = []
    nrr = latest["net_revenue_retention_pct"]
    churn = latest["gross_churn_rate_pct"]
    ltv_cac = latest["ltv_cac_ratio"]
    trial_conv = latest["trial_conversion_pct"]

    if nrr >= 120:
        checks.append(f"  ✅  Net Revenue Retention: {nrr:.1f}% — excellent (>120% = best-in-class)")
    elif nrr >= 100:
        checks.append(f"  🔄  Net Revenue Retention: {nrr:.1f}% — healthy (>100%) but expansion could be stronger")
    else:
        checks.append(f"  ⚠️  Net Revenue Retention: {nrr:.1f}% — below 100%, losing more than gaining from existing base")

    if churn <= 2.0:
        checks.append(f"  ✅  Gross Churn: {churn:.2f}% — strong retention")
    elif churn <= 3.5:
        checks.append(f"  🔄  Gross Churn: {churn:.2f}% — acceptable but worth investigating drivers")
    else:
        checks.append(f"  ⚠️  Gross Churn: {churn:.2f}% — elevated, needs immediate attention")

    if ltv_cac >= 3.0:
        checks.append(f"  ✅  LTV/CAC: {ltv_cac:.1f}x — strong unit economics (>3x = healthy)")
    elif ltv_cac >= 1.5:
        checks.append(f"  🔄  LTV/CAC: {ltv_cac:.1f}x — break-even territory, monitor closely")
    else:
        checks.append(f"  ⚠️  LTV/CAC: {ltv_cac:.1f}x — unsustainable, reduce CAC or improve retention")

    if trial_conv >= 25:
        checks.append(f"  ✅  Trial Conversion: {trial_conv:.1f}% — excellent product-led conversion")
    elif trial_conv >= 15:
        checks.append(f"  🔄  Trial Conversion: {trial_conv:.1f}% — decent but room to optimise onboarding")
    else:
        checks.append(f"  ⚠️  Trial Conversion: {trial_conv:.1f}% — low, investigate activation bottlenecks")

    for check in checks:
        print(check)

    conn.close()
    print(f"\n{'='*75}")
    print("  Dashboard complete.")
    print(f"{'='*75}\n")


if __name__ == "__main__":
    main()

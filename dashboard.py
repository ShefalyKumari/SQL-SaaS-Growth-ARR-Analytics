import duckdb
from tabulate import tabulate

DB_PATH = "saas_analytics.db"

def format_currency(val):
    if val is None:
        return "$0"
    return f"${val:,.0f}"

def render_dashboard():
    conn = duckdb.connect(DB_PATH)
    
    # 1. Register view
    with open("views/01_arr_health_dashboard_view.sql", "r") as f:
        conn.execute(f.read())

    # 2. Executive KPIs
    kpi_query = """
    SELECT 
        MAX(ending_mrr_usd) AS current_mrr,
        MAX(annualized_run_rate_arr_usd) AS current_arr,
        ROUND(AVG(expansion_rate_pct), 1) AS avg_expansion_pct,
        ROUND(AVG(mrr_churn_rate_pct), 2) AS avg_churn_pct
    FROM v_arr_health_executive_dashboard;
    """
    kpis = conn.execute(kpi_query).fetchone()

    # 3. Monthly Waterfall Data
    df_waterfall = conn.execute("""
        SELECT 
            report_month AS Month,
            ROUND(new_mrr_usd, 0) AS "New",
            ROUND(expansion_mrr_usd, 0) AS "Expansion",
            ROUND(churn_mrr_usd, 0) AS "Churn",
            ROUND(net_new_mrr_usd, 0) AS "Net New",
            ROUND(ending_mrr_usd, 0) AS "Ending MRR",
            ROUND(annualized_run_rate_arr_usd, 0) AS "ARR",
            arr_health_status AS "Health Status"
        FROM v_arr_health_executive_dashboard
        ORDER BY report_month
    """).df()

    # Apply currency format
    currency_cols = ["New", "Expansion", "Churn", "Net New", "Ending MRR", "ARR"]
    for col in currency_cols:
        df_waterfall[col] = df_waterfall[col].apply(format_currency)

    # Shorten Health Status text for compact display
    df_waterfall["Health Status"] = df_waterfall["Health Status"].str.replace("OPTIMAL (<1% Churn)", "OPTIMAL", regex=False)
    df_waterfall["Health Status"] = df_waterfall["Health Status"].str.replace("HEALTHY (Low Churn)", "HEALTHY", regex=False)

    # 4. Funnel Metrics (Transposed for clean vertical display)
    with open("queries/02_funnel_conversion.sql", "r") as f:
        funnel_df = conn.execute(f.read()).df()

    conn.close()

    # --- Render Clean Layout ---
    print("\n" + "=" * 76)
    print("         B2B SAAS ARR & REVENUE HEALTH EXECUTIVE DASHBOARD")
    print("=" * 76)
    
    # Section 1: Topline KPIs Cards
    print("\n[ 1. EXECUTIVE SUMMARY KPIs ]")
    kpi_table = [
        ["Current Ending MRR", format_currency(kpis[0]), "Avg Expansion Rate", f"{kpis[2]}%"],
        ["Annualized Run Rate (ARR)", format_currency(kpis[1]), "Avg Monthly Churn", f"{kpis[3]}%"]
    ]
    print(tabulate(kpi_table, headers=["Metric", "Value", "Benchmark", "Rate"], tablefmt="rounded_grid"))

    # Section 2: Revenue Waterfall
    print("\n[ 2. MONTHLY MRR & ARR WATERFALL ]")
    print(tabulate(df_waterfall, headers="keys", tablefmt="simple_grid", showindex=False))

    # Section 3: PLG Funnel Breakdown (Transposed key-value format prevents horizontal overflow)
    print("\n[ 3. PRODUCT-LED GROWTH (PLG) FUNNEL EFFICIENCY ]")
    row = funnel_df.iloc[0]
    funnel_summary = [
        ["Total Signups", f"{int(row['total_signups']):,}", "Top-of-Funnel Baseline"],
        ["Product Activated", f"{int(row['total_activated']):,} ({row['signup_to_activation_pct']}%)", "Activation Rate"],
        ["Trial Started", f"{int(row['total_trial']):,} ({row['activation_to_trial_pct']}%)", "Trial Adoption Rate"],
        ["Converted to Paid", f"{int(row['total_paid']):,} ({row['trial_to_paid_pct']}%)", "Trial-to-Paid Rate"],
        ["Overall Funnel Conversion", f"{row['overall_funnel_conversion_pct']}%", "End-to-End Conversion"],
        ["Avg Time to Activation", f"{row['avg_hours_to_activation']} hrs", "Activation Velocity"],
        ["Avg Time to Conversion", f"{row['avg_days_to_conversion']} days", "Sales Cycle Velocity"]
    ]
    print(tabulate(funnel_summary, headers=["Funnel Stage", "Volume / Rate", "Metric Type"], tablefmt="rounded_grid"))
    print("=" * 76 + "\n")

if __name__ == "__main__":
    render_dashboard()
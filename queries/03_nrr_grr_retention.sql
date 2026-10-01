WITH cohort_initial_revenue AS (
    SELECT 
        account_id,
        DATE_TRUNC('month', event_date) AS cohort_month,
        mrr_delta_usd AS baseline_mrr
    FROM fact_subscription_events
    WHERE event_type = 'New_Paid'
),

cohort_sizes AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT account_id) AS cohort_accounts,
        SUM(baseline_mrr) AS starting_mrr
    FROM cohort_initial_revenue
    GROUP BY cohort_month
),

cohort_monthly_balance AS (
    SELECT 
        c.cohort_month,
        DATE_TRUNC('month', e.event_date) AS activity_month,
        (EXTRACT(year FROM e.event_date) - EXTRACT(year FROM c.cohort_month)) * 12 +
        (EXTRACT(month FROM e.event_date) - EXTRACT(month FROM c.cohort_month)) AS period_offset,
        SUM(e.mrr_delta_usd) AS period_delta
    FROM fact_subscription_events e
    JOIN cohort_initial_revenue c ON e.account_id = c.account_id
    GROUP BY c.cohort_month, DATE_TRUNC('month', e.event_date), period_offset
),

cohort_cumulative AS (
    SELECT 
        cs.cohort_month,
        cs.cohort_accounts,
        cs.starting_mrr,
        cmb.period_offset,
        SUM(cmb.period_delta) OVER (
            PARTITION BY cs.cohort_month 
            ORDER BY cmb.period_offset 
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cohort_ending_mrr
    FROM cohort_sizes cs
    JOIN cohort_monthly_balance cmb ON cs.cohort_month = cmb.cohort_month
)

SELECT 
    STRFTIME(cohort_month, '%Y-%m') AS cohort,
    cohort_accounts,
    ROUND(starting_mrr, 2) AS starting_mrr_usd,
    period_offset AS month_offset,
    ROUND(cohort_ending_mrr, 2) AS cohort_mrr_usd,
    -- NRR = Current Ending MRR / Baseline Starting MRR * 100
    ROUND(100.0 * cohort_ending_mrr / starting_mrr, 1) AS nrr_percentage,
    -- GRR = LEAST(Current Ending MRR, Baseline Starting MRR) / Baseline Starting MRR * 100
    ROUND(100.0 * LEAST(cohort_ending_mrr, starting_mrr) / starting_mrr, 1) AS grr_percentage
FROM cohort_cumulative
ORDER BY cohort_month, period_offset;
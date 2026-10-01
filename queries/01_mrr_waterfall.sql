WITH monthly_mrr_components AS (
    SELECT 
        STRFTIME(DATE_TRUNC('month', event_date), '%Y-%m') AS activity_month,
        COALESCE(SUM(CASE WHEN event_type = 'New_Paid' THEN mrr_delta_usd END), 0.0) AS new_mrr,
        COALESCE(SUM(CASE WHEN event_type = 'Expansion' THEN mrr_delta_usd END), 0.0) AS expansion_mrr,
        COALESCE(SUM(CASE WHEN event_type = 'Contraction' THEN ABS(mrr_delta_usd) END), 0.0) AS contraction_mrr,
        COALESCE(SUM(CASE WHEN event_type = 'Churn' THEN ABS(mrr_delta_usd) END), 0.0) AS churn_mrr
    FROM fact_subscription_events
    GROUP BY DATE_TRUNC('month', event_date)
),

mrr_waterfall AS (
    SELECT 
        activity_month,
        new_mrr,
        expansion_mrr,
        contraction_mrr,
        churn_mrr,
        (new_mrr + expansion_mrr - contraction_mrr - churn_mrr) AS net_new_mrr
    FROM monthly_mrr_components
)

SELECT 
    activity_month,
    ROUND(new_mrr, 2) AS new_mrr_usd,
    ROUND(expansion_mrr, 2) AS expansion_mrr_usd,
    ROUND(contraction_mrr, 2) AS contraction_mrr_usd,
    ROUND(churn_mrr, 2) AS churn_mrr_usd,
    ROUND(net_new_mrr, 2) AS net_new_mrr_usd,
    ROUND(SUM(net_new_mrr) OVER (ORDER BY activity_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS ending_mrr_usd,
    ROUND(100.0 * expansion_mrr / NULLIF(new_mrr + expansion_mrr, 0), 1) AS expansion_share_pct
FROM mrr_waterfall
ORDER BY activity_month;
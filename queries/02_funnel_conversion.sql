WITH account_stages AS (
    SELECT 
        account_id,
        MIN(CASE WHEN stage = 'Signup' THEN event_timestamp END) AS signup_time,
        MIN(CASE WHEN stage = 'Product_Activated' THEN event_timestamp END) AS activated_time,
        MIN(CASE WHEN stage = 'Trial_Started' THEN event_timestamp END) AS trial_time,
        MIN(CASE WHEN stage = 'Converted_Paid' THEN event_timestamp END) AS paid_time
    FROM fact_funnel_events
    GROUP BY account_id
),

funnel_counts AS (
    SELECT 
        COUNT(signup_time) AS total_signups,
        COUNT(activated_time) AS total_activated,
        COUNT(trial_time) AS total_trial,
        COUNT(paid_time) AS total_paid,
        AVG(EXTRACT(EPOCH FROM (activated_time - signup_time)) / 3600.0) AS avg_hours_to_activate,
        AVG(EXTRACT(EPOCH FROM (paid_time - signup_time)) / 24.0 / 3600.0) AS avg_days_to_paid
    FROM account_stages
)

SELECT 
    total_signups,
    total_activated,
    total_trial,
    total_paid,
    ROUND(100.0 * total_activated / total_signups, 1) AS signup_to_activation_pct,
    ROUND(100.0 * total_trial / total_activated, 1) AS activation_to_trial_pct,
    ROUND(100.0 * total_paid / total_trial, 1) AS trial_to_paid_pct,
    ROUND(100.0 * total_paid / total_signups, 1) AS overall_funnel_conversion_pct,
    ROUND(avg_hours_to_activate, 1) AS avg_hours_to_activation,
    ROUND(avg_days_to_paid, 1) AS avg_days_to_conversion
FROM funnel_counts;
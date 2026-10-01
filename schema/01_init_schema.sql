DROP TABLE IF EXISTS fact_funnel_events;
DROP TABLE IF EXISTS fact_subscription_events;
DROP TABLE IF EXISTS dim_subscription_history;
DROP TABLE IF EXISTS dim_plans;
DROP TABLE IF EXISTS dim_accounts;

-- 1. Dim Plans (Tiers)
CREATE TABLE dim_plans (
    plan_id VARCHAR(16) PRIMARY KEY,
    plan_tier VARCHAR(32) NOT NULL, -- Starter, Professional, Enterprise
    monthly_price_usd NUMERIC(10, 2) NOT NULL,
    max_seats INTEGER NOT NULL
);

-- 2. Dim Accounts (Entity)
CREATE TABLE dim_accounts (
    account_id VARCHAR(16) PRIMARY KEY,
    company_name VARCHAR(64) NOT NULL,
    industry VARCHAR(32) NOT NULL,
    acquisition_channel VARCHAR(32) NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- 3. Dim Subscription History (SCD Type 2: Plan Upgrades/Downgrades/Status)
CREATE TABLE dim_subscription_history (
    history_id VARCHAR(16) PRIMARY KEY,
    account_id VARCHAR(16) NOT NULL REFERENCES dim_accounts(account_id),
    plan_id VARCHAR(16) NOT NULL REFERENCES dim_plans(plan_id),
    status VARCHAR(24) NOT NULL CHECK (status IN ('Active', 'Cancelled', 'Trial')),
    mrr_usd NUMERIC(10, 2) NOT NULL,
    valid_from DATE NOT NULL,
    valid_to DATE, -- NULL indicates current active state
    is_current BOOLEAN NOT NULL DEFAULT TRUE
);

-- 4. Fact Subscription Events (Log of billing/lifecycle events)
CREATE TABLE fact_subscription_events (
    event_id VARCHAR(16) PRIMARY KEY,
    account_id VARCHAR(16) NOT NULL REFERENCES dim_accounts(account_id),
    event_type VARCHAR(24) NOT NULL CHECK (event_type IN ('New_Paid', 'Expansion', 'Contraction', 'Churn', 'Renewal')),
    event_date DATE NOT NULL,
    mrr_delta_usd NUMERIC(10, 2) NOT NULL
);

-- 5. Fact Product Funnel Events (Product-Led Growth Funnel)
CREATE TABLE fact_funnel_events (
    funnel_event_id VARCHAR(16) PRIMARY KEY,
    account_id VARCHAR(16) NOT NULL REFERENCES dim_accounts(account_id),
    stage VARCHAR(32) NOT NULL CHECK (stage IN ('Signup', 'Product_Activated', 'Trial_Started', 'Converted_Paid')),
    event_timestamp TIMESTAMP NOT NULL
);
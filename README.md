# SaaS Product Growth, Funnel Conversion & ARR Health Dashboard

A production-grade SQL dimensional data warehouse and revenue analytics engine modeling B2B SaaS lifecycle events, Product-Led Growth (PLG) conversion funnels, MRR waterfalls, and cohort-based Net Revenue Retention (NRR).

---

## Relational Dimensional Model (Star Schema)

```text
[dim_accounts] 1 ────< [fact_funnel_events]
       │
       ├──────── 1 ────< [dim_subscription_history (SCD Type 2)] >──── 1 [dim_plans]
       │
       └──────── 1 ────< [fact_subscription_events]
import random
from datetime import date, datetime, timedelta
import duckdb

DB_PATH = "saas_analytics.db"

def seed_database():
    conn = duckdb.connect(DB_PATH)
    
    with open("schema/01_init_schema.sql", "r") as f:
        schema_sql = f.read()
    conn.execute(schema_sql)
    print("SaaS schema initialized successfully.")

    random.seed(42)

    # 1. Plans
    plans = [
        ("PLAN-START", "Starter", 99.00, 5),
        ("PLAN-PRO", "Professional", 299.00, 20),
        ("PLAN-ENT", "Enterprise", 999.00, 100),
    ]
    conn.executemany("INSERT INTO dim_plans VALUES (?, ?, ?, ?)", plans)

    # 2. Accounts (100 Accounts created between Jan 2025 and May 2025)
    channels = ["Product Hunt", "Inbound SEO", "Google Ads", "Outbound SDR", "Referral"]
    industries = ["FinTech", "HealthTech", "E-Commerce", "Cybersecurity", "DevTools"]
    
    base_date = date(2025, 1, 1)
    accounts = []
    for i in range(1, 101):
        acc_id = f"ACC-{i:04d}"
        created_dt = base_date + timedelta(days=random.randint(0, 120))
        created_ts = datetime(created_dt.year, created_dt.month, created_dt.day, random.randint(8, 18), random.randint(0, 59))
        accounts.append((acc_id, f"Company_{i}", random.choice(industries), random.choice(channels), created_ts))

    conn.executemany("INSERT INTO dim_accounts VALUES (?, ?, ?, ?, ?)", accounts)

    # 3. Product Funnel Events & Subscriptions
    funnel_events = []
    sub_history = []
    sub_events = []
    
    fe_counter = 1
    sh_counter = 1
    se_counter = 1

    for acc in accounts:
        acc_id = acc[0]
        signup_ts = acc[4]
        signup_date = signup_ts.date()

        # Step 1: Signup
        funnel_events.append((f"FE-{fe_counter:06d}", acc_id, "Signup", signup_ts))
        fe_counter += 1

        # Step 2: Product Activation (75% of signups)
        activated = random.random() < 0.75
        if activated:
            act_ts = signup_ts + timedelta(hours=random.randint(1, 48))
            funnel_events.append((f"FE-{fe_counter:06d}", acc_id, "Product_Activated", act_ts))
            fe_counter += 1

            # Step 3: Trial Started (80% of activated)
            trial = random.random() < 0.80
            if trial:
                trial_ts = act_ts + timedelta(days=random.randint(1, 4))
                funnel_events.append((f"FE-{fe_counter:06d}", acc_id, "Trial_Started", trial_ts))
                fe_counter += 1

                # Step 4: Converted to Paid (50% of trials convert)
                if random.random() < 0.50:
                    paid_ts = trial_ts + timedelta(days=14)
                    paid_date = paid_ts.date()
                    if paid_date <= date(2025, 6, 30):
                        funnel_events.append((f"FE-{fe_counter:06d}", acc_id, "Converted_Paid", paid_ts))
                        fe_counter += 1

                        # Initial Subscription
                        initial_plan = random.choice([("PLAN-START", 99.00), ("PLAN-PRO", 299.00)])
                        sub_events.append((f"SE-{se_counter:06d}", acc_id, "New_Paid", paid_date, initial_plan[1]))
                        se_counter += 1

                        # Track Subscription Lifecycle (Expansion, Contraction, Churn)
                        upgrade_date = paid_date + timedelta(days=random.randint(30, 60))
                        if random.random() < 0.35 and upgrade_date <= date(2025, 6, 30):
                            # Upgraded to Enterprise
                            sub_history.append((f"SH-{sh_counter:06d}", acc_id, initial_plan[0], "Active", initial_plan[1], paid_date, upgrade_date, False))
                            sh_counter += 1

                            delta = 999.00 - initial_plan[1]
                            sub_events.append((f"SE-{se_counter:06d}", acc_id, "Expansion", upgrade_date, delta))
                            se_counter += 1

                            sub_history.append((f"SH-{sh_counter:06d}", acc_id, "PLAN-ENT", "Active", 999.00, upgrade_date, None, True))
                            sh_counter += 1
                        elif random.random() < 0.15 and upgrade_date <= date(2025, 6, 30):
                            # Churned
                            sub_history.append((f"SH-{sh_counter:06d}", acc_id, initial_plan[0], "Active", initial_plan[1], paid_date, upgrade_date, False))
                            sh_counter += 1

                            sub_events.append((f"SE-{se_counter:06d}", acc_id, "Churn", upgrade_date, -initial_plan[1]))
                            se_counter += 1

                            sub_history.append((f"SH-{sh_counter:06d}", acc_id, initial_plan[0], "Cancelled", 0.00, upgrade_date, None, True))
                            sh_counter += 1
                        else:
                            # Remained on initial plan
                            sub_history.append((f"SH-{sh_counter:06d}", acc_id, initial_plan[0], "Active", initial_plan[1], paid_date, None, True))
                            sh_counter += 1

    conn.executemany("INSERT INTO fact_funnel_events VALUES (?, ?, ?, ?)", funnel_events)
    conn.executemany("INSERT INTO dim_subscription_history VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sub_history)
    conn.executemany("INSERT INTO fact_subscription_events VALUES (?, ?, ?, ?, ?)", sub_events)

    print(f"SaaS dataset seeded successfully:")
    print(f" - Accounts:              {len(accounts)}")
    print(f" - Funnel Events:         {len(funnel_events)}")
    print(f" - Subscription Changes:  {len(sub_history)}")
    print(f" - Subscription Events:   {len(sub_events)}")
    conn.close()

if __name__ == "__main__":
    seed_database()
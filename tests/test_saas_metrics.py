import duckdb
import pytest

DB_PATH = "saas_analytics.db"

@pytest.fixture
def db_conn():
    conn = duckdb.connect(DB_PATH)
    yield conn
    conn.close()

def test_database_populated(db_conn):
    acc_count = db_conn.execute("SELECT COUNT(*) FROM dim_accounts").fetchone()[0]
    fe_count = db_conn.execute("SELECT COUNT(*) FROM fact_funnel_events").fetchone()[0]
    se_count = db_conn.execute("SELECT COUNT(*) FROM fact_subscription_events").fetchone()[0]
    assert acc_count == 100
    assert fe_count > 150
    assert se_count > 0

def test_mrr_waterfall_balances_positive(db_conn):
    with open("queries/01_mrr_waterfall.sql", "r") as f:
        query = f.read()
    df = db_conn.execute(query).df()
    
    assert len(df) > 0
    assert (df["ending_mrr_usd"] > 0).all()
    assert (df["new_mrr_usd"] >= 0).all()

def test_funnel_conversion_rates_realistic(db_conn):
    with open("queries/02_funnel_conversion.sql", "r") as f:
        query = f.read()
    df = db_conn.execute(query).df()
    
    assert len(df) == 1
    row = df.iloc[0]
    assert row["total_signups"] >= row["total_activated"]
    assert row["total_activated"] >= row["total_trial"]
    assert row["total_trial"] >= row["total_paid"]
    assert 0.0 < row["overall_funnel_conversion_pct"] <= 100.0

def test_nrr_grr_calculations(db_conn):
    with open("queries/03_nrr_grr_retention.sql", "r") as f:
        query = f.read()
    df = db_conn.execute(query).df()
    
    assert len(df) > 0
    # Month 0 NRR and GRR must always equal exactly 100.0%
    m0_rows = df[df["month_offset"] == 0]
    assert (m0_rows["nrr_percentage"] == 100.0).all()
    assert (m0_rows["grr_percentage"] == 100.0).all()
    # GRR can never exceed 100.0% by definition
    assert (df["grr_percentage"] <= 100.0).all()
import sys
import duckdb
from tabulate import tabulate

DB_PATH = "saas_analytics.db"

def run_sql_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        query = f.read()

    conn = duckdb.connect(DB_PATH)
    df = conn.execute(query).df()
    conn.close()

    print(f"\n=== Executing: {file_path} ===")
    print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_query.py <path_to_sql_file>")
        sys.exit(1)
    run_sql_file(sys.argv[1])
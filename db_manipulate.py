import sqlite3
import argparse

def drop_daily_rows_by_date(db_path: str, target_date: str):
    """Delete rows from daily_data table for a specific date."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("DELETE FROM daily_data WHERE 日期 = ?", (target_date,))
        conn.commit()
        print(f"Deleted {cur.rowcount} rows for date {target_date}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Delete rows from the daily_data table for a specific date.")
    parser.add_argument("db_path", type=str, help="Path to the SQLite database file.")
    parser.add_argument("target_date", type=str, help="The date string to match for deletion (e.g., '2023-10-27').")
    
    args = parser.parse_args()
    drop_daily_rows_by_date(args.db_path, args.target_date)

# usage: python db_manipulate.py ./stock_data.db 2026-01-16

if __name__ == "__main__":
    main()
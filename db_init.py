import akshare as ak
import sqlite3
import pandas as pd
import time
import argparse
import re
from typing import Optional

def get_a_share_list():
    conn = sqlite3.connect("stock_data.db")
    df = pd.read_sql_query("SELECT code, name FROM stocks", conn)
    conn.close()
    if not df.empty:
        return df
    return None

def sanitize_table_name(code: str) -> str:
    return f"stock_{re.sub(r'[^0-9A-Za-z_]', '_', str(code))}"


def fetch_and_save_all(limit: Optional[int], start_date: str, end_date: str, sleep_sec: float):
    df_list = get_a_share_list()
    code_col, name_col = 'code','name'

    conn = sqlite3.connect("stock_data.db")
    try:
        total = len(df_list)
        for idx, row in df_list.iterrows():
            code = str(row[code_col]).strip()
            name = str(row[name_col]).strip() if name_col else code
            i = idx + 1
            try:
                print(f"[{i}/{total}] Fetching {code} {name}...", end=" ")
                hist = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
                if isinstance(hist, pd.DataFrame) and not hist.empty:
                    hist.to_sql(name, conn, if_exists="replace", index=False)
                    print("saved")
                else:
                    print("no data")
            except KeyboardInterrupt:
                print("\nInterrupted by user. Exiting.")
                break
            except Exception as e:
                print(f"failed: {e}")
            if limit is not None and i >= limit:
                print(f"Reached limit {limit}; stopping.")
                break
            time.sleep(sleep_sec)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Fetch all A-share historical data and save to SQLite.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of stocks to fetch (for testing)")
    parser.add_argument("--start", default="20200101", help="Start date YYYYMMDD")
    parser.add_argument("--end", default="20251231", help="End date YYYYMMDD")
    parser.add_argument("--sleep", type=float, default=0.3, help="Seconds to sleep between requests")
    args = parser.parse_args()

    fetch_and_save_all(limit=args.limit, start_date=args.start, end_date=args.end, sleep_sec=args.sleep)


if __name__ == "__main__":
    main()
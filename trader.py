import akshare as ak
import sqlite3
import pandas as pd

stock_code = "600362" # 江西铜业
print(f"Fetching data for {stock_code}...")

df = ak.stock_zh_a_hist(
    symbol=stock_code,
    period="daily",
    start_date="20200101",
    end_date="20251231",
    adjust="qfq",
)

conn = sqlite3.connect("stock_data.db")

try:
    df.to_sql("江西铜业", conn, if_exists="replace", index=False)
    print("保存成功")

    check_df = pd.read_sql("SELECT * FROM 江西铜业 LIMIT 5", conn)
    print("\nFirst 5 rows in Database:")
    print(check_df)

finally:
    conn.close()
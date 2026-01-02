import akshare as ak
import sqlite3
import pandas as pd

stock_code = "688981"

conn = sqlite3.connect("stock_data.db")

try:
    query = f"""
        SELECT * FROM stocks where code={stock_code}
    """
    df = pd.read_sql(query, conn)
    name = df['name'][0]

    print(f"Fetching data for {name}...")
    df = ak.stock_zh_a_hist(
        symbol=stock_code,
        period="daily",
        start_date="20200101",
        end_date="20251231",
        adjust="qfq",
    )

    df.to_sql(name, conn, if_exists="replace", index=False)
    print("保存成功")

    #check_df = pd.read_sql("SELECT * FROM 江西铜业 LIMIT 5", conn)
    #print("\nFirst 5 rows in Database:")
    #print(check_df)

finally:
    conn.close()
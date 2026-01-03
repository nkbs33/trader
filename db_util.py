
import sqlite3
import pandas as pd


class DatabaseUtil:
    def __init__(self, path="stock_data.db"):
        self.db_path = path
        self.candle_columns = ["日期","开盘","最高","最低","收盘","成交量"]

    def get_table_names(self, conn):
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        return [row[0] for row in cur.fetchall()]

    def fetch_recent_df(self, conn, table_name, day_count=30):
        q = f"SELECT * FROM {table_name} ORDER BY 日期 DESC LIMIT {day_count}"
        df = pd.read_sql(q, conn)
        if df.empty:
            return df
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期").reset_index(drop=True)
        return df
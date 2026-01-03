import sqlite3
import pandas as pd
import akshare as ak
import time
from typing import Optional
import os
import pickle

class StockDatabase:
    def __init__(self, path="stock_data.db"):
        self.db_path = path
        self.candle_columns = ["日期","开盘","最高","最低","收盘","成交量"]
        self.conn = sqlite3.connect(self.db_path)

    def __del__(self):
        self.conn.close()

    def get_a_stock_info(self):
        return ak.stock_zh_a_spot_em() 

    def get_a_share_list_local(self,):
        return pd.read_sql_query("SELECT code, name FROM stocks", self.conn)


    def fetch_and_save_all_daily_data(self, limit: Optional[int], start_date: str, end_date: str, sleep_sec: float):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_data (
                stock TEXT NOT NULL,
                日期 TEXT NOT NULL,
                开盘 REAL,
                最高 REAL,
                最低 REAL,
                收盘 REAL,
                成交量 REAL,
                PRIMARY KEY(stock, 日期)
            )
            """
        )
        self.conn.commit()

        df_list = self.get_a_share_list()

        total = len(df_list)
        for idx, row in df_list.iterrows():
            code = str(row['code']).strip()
            name = str(row['name']).strip()
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
                    # Only keep required columns
                    required_cols = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]
                    if not all(col in hist.columns for col in required_cols):
                        print("missing columns; skipped")
                        continue
                    hist = hist[required_cols].copy()
                    hist["stock"] = name
                    # Reorder columns to match table
                    hist = hist[["stock"] + required_cols]
                    # Insert into daily_data
                    hist.to_sql("daily_data", self.conn, if_exists="append", index=False)
                    print("saved to daily_data")
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
    
    def get_daily_data(self, stock_name, day_count=30):
        q = f"SELECT * FROM daily_data WHERE stock = ? ORDER BY 日期 DESC LIMIT ?"
        df = pd.read_sql(q, self.conn, params=(stock_name, day_count))
        if df.empty:
            return df
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期").reset_index(drop=True)
        return df
    
    def get_stock_detailed_info(self, stock_code="000001"):
        try:
            info_df = ak.stock_individual_info_em(symbol=stock_code)
            return info_df
        except Exception as e:
            print(f"获取 {stock_code} 信息失败: {e}")
            return None
        
    def download_stock_data(self, filename="stock_data.pkl"):
        import pickle
        df = self.get_a_stock_info()
        with open(filename, "wb") as f:
            pickle.dump(df, f)

    def update_stock_info(self):
        
        cur = self.conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                code TEXT PRIMARY KEY,
                name TEXT,
                mv TEXT,
                circ_mv TEXT
            )
        ''')
        if os.path.exists("stock_data.pkl"):
            with open("stock_data.pkl", "rb") as f:
                df = pickle.load(f)
        else:
            df = self.get_a_stock_info()
#       
        cnt = 0
        for code in df['代码']:
            print(f"{code}, {df['名称'][cnt]}")
            cur.execute("INSERT OR IGNORE INTO stocks (code) VALUES (?)", (code,))
            cur.execute(
                "UPDATE stocks SET name=?, mv=?, circ_mv=? WHERE code=?",
                (df['名称'][cnt], df['总市值'][cnt], df['流通市值'][cnt], code),
            )
            self.conn.commit()
            cnt += 1

    def daily_update(self):
        self.download_stock_data()
        self.update_stock_info()

    def get_market_value_by_code(self, code):
        """
        Returns the market value (mv) for the given stock code as a float.
        Returns None if not found or not convertible.
        """
        cur = self.conn.cursor()
        cur.execute("SELECT mv FROM stocks WHERE code = ?", (code,))
        row = cur.fetchone()
        if row and row[0] is not None:
            try:
                # Remove commas and convert to float
                return float(str(row[0]).replace(',', ''))
            except Exception:
                return None
        return None

if __name__=='__main__':
    db = StockDatabase()
    print(db.get_stock_detailed_info('000005'))
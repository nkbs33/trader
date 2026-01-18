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
                涨跌幅 REAL,
                振幅 REAL,
                换手率 REAL,
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
                hist:pd.DataFrame = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
                if isinstance(hist, pd.DataFrame) and not hist.empty:
                    required_cols = ["日期", "开盘", "最高", "最低", "收盘", "成交量", "涨跌幅", "振幅", "换手率"]
                    if not all(col in hist.columns for col in required_cols):
                        print("missing columns; skipped")
                        continue
                    hist = hist[required_cols].copy()
                    hist["stock"] = name
                    # Reorder columns to match table
                    hist = hist[["stock"] + required_cols]
                    # Insert into daily_data
                    hist.to_sql("daily_data", self.conn, if_exists="replace", index=False)
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
    
    def fetch_daily_data(self, limit: Optional[int], sleep_sec: float):
        import datetime
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
                涨跌幅 REAL,
                振幅 REAL,
                PRIMARY KEY(stock, 日期)
            )
            """
        )
        self.conn.commit()

        df_list = self.get_a_share_list_local()

        total = len(df_list)
        today = datetime.date.today().strftime('%Y%m%d')
        for idx, row in df_list.iterrows():
            code = str(row['code']).strip()
            name = str(row['name']).strip()
            i = idx + 1
            # 查询该股票在daily_data表中的最后日期
            cur = self.conn.cursor()
            cur.execute("SELECT MAX(日期) FROM daily_data WHERE stock = ?", (name,))
            last_date = cur.fetchone()[0]
            if last_date is None:
                start_date = '20200101'
            else:
                # 否则从最后日期的下一天开始
                last_date_dt = datetime.datetime.strptime(last_date, '%Y-%m-%d')
                start_date = (last_date_dt + datetime.timedelta(days=1)).strftime('%Y%m%d')
            end_date = today
            if start_date > end_date:
                print(f"[{i}/{total}] {code} {name} 已是最新，无需更新")
                continue
            try:
                print(f"[{i}/{total}] Fetching {code} {name} from {start_date} to {end_date}...", end=" ")
                hist:pd.DataFrame = ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
                # print(hist)
                if isinstance(hist, pd.DataFrame) and not hist.empty:
                    required_cols = ["日期", "开盘", "最高", "最低", "收盘", "成交量", "涨跌幅", "振幅"]
                    if not all(col in hist.columns for col in required_cols):
                        print("missing columns; skipped")
                        continue
                    hist = hist[required_cols].copy()
                    hist["stock"] = name
                    # Reorder columns to match table
                    hist = hist[["stock"] + required_cols]
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
    
    def query_daily_data(self, stock_name, day_count=30):
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

    def calculate_pct_and_amp_for_all(self):
        """
        计算所有股票的涨跌幅和振幅，并更新到 daily_data 表。
        涨跌幅 = (收盘 - 前一日收盘) / 前一日收盘 * 100
        振幅 = (最高 - 最低) / 前一日收盘 * 100
        """
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT stock FROM daily_data")
        stocks = [row[0] for row in cur.fetchall()]
        for stock in stocks:
            df = pd.read_sql(
                "SELECT 日期, 开盘, 最高, 最低, 收盘 FROM daily_data WHERE stock = ? ORDER BY 日期 ASC",
                self.conn, params=(stock,)
            )
            if df.shape[0] < 2:
                continue
            df["前收盘"] = df["收盘"].shift(1)
            df["涨跌幅"] = ((df["收盘"] - df["前收盘"]) / df["前收盘"] * 100).round(3)
            df["振幅"] = ((df["最高"] - df["最低"]) / df["前收盘"] * 100).round(3)
            for idx, row in df.iterrows():
                if pd.isna(row["前收盘"]):
                    continue
                cur.execute(
                    "UPDATE daily_data SET 涨跌幅=?, 振幅=? WHERE stock=? AND 日期=?",
                    (row["涨跌幅"], row["振幅"], stock, row["日期"])
                )
            self.conn.commit()

if __name__=='__main__':
    import sys
    db = StockDatabase()
    if len(sys.argv) < 2:
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "fetch":
        limit = None
        if len(sys.argv) > 2:
            try:
                limit = int(sys.argv[2])
            except Exception:
                print("Invalid limit, using all stocks.")
                limit = None
        db.fetch_daily_data(limit=limit, sleep_sec=0.01)
    elif cmd == "info" and len(sys.argv) > 2:
        code = sys.argv[2]
        print(db.get_stock_detailed_info(code))
    elif cmd == "calc_inc":
        db.calculate_pct_and_amp_for_all()
    else:
        print("Unknown command or missing argument.")
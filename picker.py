import sqlite3
import pandas as pd
from plot import calculate_kdj
from datetime import date

from db_util import DatabaseUtil

class StockUpdater:
    pass

class StockPicker:
    db_path: str

    def __init__(self):
        self.db_path = "stock_data.db"
        self.db = DatabaseUtil(self.db_path)

    def find_stocks_with_j_below(self, threshold=12):
        conn = sqlite3.connect(self.db_path)
        tables = self.db.get_table_names(conn)
        matches = []
        day_count = 30
        count = 0
        for t in tables:
            try:
                df = self.db.fetch_recent_df(conn, t, day_count=day_count)
                if df.shape[0] < 9:
                    continue
                df = df[self.db.candle_columns]
                df = calculate_kdj(df)
                last_j = pd.to_numeric(df["J"].iloc[-1], errors="coerce")
                if pd.notna(last_j) and last_j < threshold:
                    matches.append((t, float(last_j)))
                count += 1
                if count % 100 == 0:
                    print(f"{count}/{len(tables)}")
            except Exception:
                continue
        conn.close()
        csv_name = f"matches_{date.today().isoformat()}.csv"
        pd.DataFrame(matches, columns=["name", "J"]).to_csv(csv_name, index=False)


if __name__ == "__main__":
    pick = StockPicker()
    pick.find_stocks_with_j_below(threshold=12)

import pandas as pd
from webapp.ui.plot import calculate_kdj
from datetime import date

from webapp.db.stock_db import StockDatabase

class StockPicker:
    db_path: str

    def __init__(self):
        self.db_path = "stock_data.db"
        self.db = StockDatabase(self.db_path)

    def find_stocks_with_j_below(self, cols, threshold=12):
        stock_list = self.db.get_a_share_list_local()
        stock_list = stock_list.sort_values(by="code")  # sort by code

        matches = []
        day_count = 60
        count = 0
        for idx, row in stock_list.iterrows():
            code = str(row['code']).strip()
            name = str(row['name']).strip()

            df = self.db.query_daily_data(name, day_count=day_count)
            df = df[self.db.candle_columns]
            df = calculate_kdj(df)
            
            try:
                last_j = pd.to_numeric(df["J"].iloc[-1], errors="coerce")
                if pd.notna(last_j) and last_j < threshold:
                    matches.append((code, name, float(last_j)))
            except:
                pass
            count += 1
            if count % 100 == 0:
                print(f"{count}/{len(stock_list)}")
        
        cols.append('J')
        return matches, cols

    def filter_by_market_value(self, matches,cols, min_value=None, max_value=None):
        filtered = []
        for code, name, j in matches:
            market_value = self.db.get_market_value_by_code(code)
            if market_value is None:
                continue
            if (min_value is not None and market_value < min_value):
                continue
            if (max_value is not None and market_value > max_value):
                continue
            filtered.append((code, name, j, market_value/1e8))
        
        cols.append('market_value')
        return filtered, cols
    
    @staticmethod
    def detect_high_volume_days(df, volume_col="成交量"):
        """
        Detect days where the volume is greater than 2 times the previous day's volume.
        Returns a DataFrame with a boolean column 'high_volume' indicating such days.
        """
        df = df.copy()
        df["prev_volume"] = df[volume_col].shift(1)
        df["high_volume"] = df[volume_col] > 2 * df["prev_volume"]
        return df[df["high_volume"]]

if __name__ == "__main__":
    picker = StockPicker()
    df = picker.db.query_daily_data('江西铜业', 60)
    print(StockPicker.detect_high_volume_days(df))
    

    # cols = ["code", "name"]
    # matches,cols = picker.find_stocks_with_j_below(cols, threshold=12)
    # matches,cols = picker.filter_by_market_value(matches, cols, min_value=80_0000_0000)
    
    # df = pd.DataFrame(matches, columns=cols)
    # float_cols = [col for col in ["J", "market_value"] if col in df.columns]
    # df[float_cols] = df[float_cols].astype(float).round(2)
    # csv_name = f"result/{date.today().isoformat()}.csv"
    # df.to_csv(csv_name, index=False)
    


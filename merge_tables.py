#!/usr/bin/env python3
"""Merge per-stock tables in `stock_data.db` into a single `daily_data` table.

The script will:
- create `daily_data` if missing with columns: stock, 日期, 开盘, 最高, 最低, 收盘, 成交量
- iterate over user tables (skipping metadata tables)
- validate each table has the required columns
- insert rows using `INSERT OR REPLACE` to avoid duplicates

Usage:
    python merge_tables.py [--db stock_data.db] [--drop] [--limit N]

"""
import sqlite3
import argparse
import re
from typing import List


REQUIRED_COLS = ["日期", "开盘", "最高", "最低", "收盘", "成交量"]


def quote_ident(name: str) -> str:
    # simple identifier quoting for SQLite
    return '"' + name.replace('"', '""') + '"'


def get_user_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [r[0] for r in cur.fetchall()]
    # exclude helper tables
    exclude = {"stocks", "recent_queries", "daily_data"}
    return [t for t in tables if t not in exclude]


def table_has_columns(conn: sqlite3.Connection, table: str, required: List[str]) -> bool:
    cur = conn.execute(f"PRAGMA table_info({quote_ident(table)})")
    cols = [r[1] for r in cur.fetchall()]
    return all(col in cols for col in required)


def create_daily_table(conn: sqlite3.Connection):
    conn.execute(
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
    conn.commit()


def merge_tables(db_path: str, drop_first: bool = False, limit: int = None, drop_source: bool = False):
    conn = sqlite3.connect(db_path)
    try:
        create_daily_table(conn)

        if drop_first:
            conn.execute("DELETE FROM daily_data")
            conn.commit()

        tables = get_user_tables(conn)
        if limit:
            tables = tables[:limit]

        total = len(tables)
        print(f"Found {total} user tables to merge")

        insert_sql = (
            "INSERT OR REPLACE INTO daily_data (stock, 日期, 开盘, 最高, 最低, 收盘, 成交量)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)"
        )

        merged_tables = []
        for idx, table in enumerate(tables, start=1):
            try:
                if not table_has_columns(conn, table, REQUIRED_COLS):
                    print(f"Skipping {table}: missing required columns")
                    continue

                q = f"SELECT {', '.join(quote_ident(c) for c in REQUIRED_COLS)} FROM {quote_ident(table)}"
                cur = conn.execute(q)
                rows = cur.fetchall()
                if not rows:
                    continue

                # prepare tuples with stock name first
                params = [(table, r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]

                # use a transaction per table
                conn.executemany(insert_sql, params)
                conn.commit()
                print(f"[{idx}/{total}] merged {len(rows)} rows from {table}")
                merged_tables.append(table)
            except Exception as e:
                print(f"Error merging {table}: {e}")
                conn.rollback()
        # optionally drop source tables that were successfully merged
        if drop_source and merged_tables:
            print(f"Dropping {len(merged_tables)} source tables...")
            for t in merged_tables:
                try:
                    conn.execute(f"DROP TABLE IF EXISTS {quote_ident(t)}")
                except Exception as e:
                    print(f"Failed to drop {t}: {e}")
            conn.commit()
            print("Dropped source tables")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Merge per-stock tables into daily_data table")
    parser.add_argument("--db", default="stock_data.db", help="SQLite DB path")
    parser.add_argument("--drop", action="store_true", help="Drop existing rows in daily_data before merging")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of tables to merge (for testing)")
    parser.add_argument("--drop-source", action="store_true", help="Drop source per-stock tables after successful merge (destructive)")
    args = parser.parse_args()

    merge_tables(args.db, drop_first=args.drop, limit=args.limit, drop_source=args.drop_source)


if __name__ == "__main__":
    main()

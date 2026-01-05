import dash
from dash import html, dcc, callback, Output, Input, State, callback_context
from dash.dependencies import ALL
import ast
import sqlite3
import pandas as pd
from datetime import datetime

def add_recent_query(query: str):
    conn = sqlite3.connect('stock_data.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS recent_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            ts TEXT
        )
    ''')
    # remove any existing entries with the same query so list stays deduplicated
    try:
        cur.execute('DELETE FROM recent_queries WHERE query = ?', (query,))
    except Exception:
        pass
    cur.execute('INSERT INTO recent_queries (query, ts) VALUES (?, ?)', (query, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()


def get_recent_queries_data(limit=10):
    conn = sqlite3.connect('stock_data.db')
    try:
        df = pd.read_sql_query(f"SELECT query FROM recent_queries ORDER BY id DESC LIMIT {limit}", conn)
        return [str(x) for x in df['query'].tolist()]
    except Exception:
        return []
    finally:
        conn.close()

def draw_recent_panel(limit=10):
    conn = sqlite3.connect('stock_data.db')
    try:
        df = pd.read_sql_query(f"SELECT query, ts FROM recent_queries ORDER BY id DESC LIMIT {limit}", conn)
    except Exception:
        df = pd.DataFrame(columns=['query', 'ts'])
    conn.close()
    items = []
    # build clickable buttons with pattern-matching ids; enumerate to keep indexes stable
    for i, (_, row) in enumerate(df.iterrows()):
        q = f"{row['query']}"
        label = f"{row['query']}  ({row['ts']})"
        btn = html.Button(label, id={'type': 'recent-query', 'index': i}, n_clicks=0, style={'width': '100%', 'textAlign': 'left', 'border': 'none', 'background': '#222', 'color': '#f5f5f5', 'padding': '6px 0'})
        items.append(html.Li(btn, style={'background': '#181818', 'color': '#f5f5f5', 'marginBottom': '2px'}))
    if not items:
        return html.Div("No recent queries yet.", style={'color': '#888'})
    return html.Ul(items, style={'background': '#181818', 'color': '#f5f5f5', 'padding': '0', 'listStyle': 'none'})

@callback(
    Output('dropdown-selection', 'value', allow_duplicate=True),
    Output('sidebar-content', 'children', allow_duplicate=True),
    Input({'type': 'recent-query', 'index': ALL}, 'n_clicks'),
    State('sidebar-tabs', 'value'),
    prevent_initial_call=True,
)
def on_recent_click(n_clicks_list, tab):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_obj = ast.literal_eval(prop_id)
        idx = int(triggered_obj.get('index', 0))
    except Exception:
        raise dash.exceptions.PreventUpdate
    
    queries = get_recent_queries_data()
    if idx < 0 or idx >= len(queries):
        raise dash.exceptions.PreventUpdate
    selected = queries[idx]
    add_recent_query(selected)
    return selected, draw_recent_panel()
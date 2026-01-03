import dash
from dash import html, dcc, callback, Output, Input, State, callback_context
from dash.dependencies import ALL
import ast
import sqlite3
import pandas as pd
from datetime import datetime

def draw_favorite_panel(limit=20):
    conn = sqlite3.connect('stock_data.db')
    try:
        df = pd.read_sql_query(f"SELECT query, ts FROM favorite_collection ORDER BY id DESC LIMIT {limit}", conn)
        # print(df)
    except Exception:
        df = pd.DataFrame(columns=['query', 'ts'])
    conn.close()
    items = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        q = f"{row['query']}"
        label = f"{row['query']}  ({row['ts']})"
        btn = html.Button(label, id={'type': 'favorite-query', 'index': i}, n_clicks=0, style={'width': '70%', 'textAlign': 'left', 'border': 'none', 'background': 'none', 'padding': '6px 0'})
        remove_btn = html.Button('Remove', id={'type': 'remove-favorite', 'index': i}, n_clicks=0, style={'marginLeft': '8px', 'color': 'red'})
        items.append(html.Li([btn, remove_btn], style={'display': 'flex', 'alignItems': 'center'}))
    if not items:
        return html.Div("No favorites yet.")
    return html.Ul(items)

@callback(
    Output('dropdown-selection', 'value', allow_duplicate=True),
    Input({'type': 'favorite-query', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def on_favorite_click(n_clicks_list):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_obj = ast.literal_eval(prop_id)
        idx = int(triggered_obj.get('index', 0))
    except Exception:
        raise dash.exceptions.PreventUpdate
    conn = sqlite3.connect('stock_data.db')
    try:
        df = pd.read_sql_query(f"SELECT query FROM favorite_collection ORDER BY id DESC LIMIT 20", conn)
        queries = [str(x) for x in df['query'].tolist()]
    except Exception:
        queries = []
    finally:
        conn.close()
    if idx < 0 or idx >= len(queries):
        raise dash.exceptions.PreventUpdate
    selected = queries[idx]
    return selected

@callback(
    Input('add-favorite-btn', 'n_clicks'),
    State('dropdown-selection', 'value'),
    State('sidebar-tabs', 'value'),
    prevent_initial_call=True
)
def add_to_favorites(n_clicks, value, tab):
    if n_clicks and value:
        add_favorite(value)

def add_favorite(query: str):
    conn = sqlite3.connect('stock_data.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS favorite_collection (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            ts TEXT
        )
    ''')
    cur.execute('DELETE FROM favorite_collection WHERE query = ?', (query,))
    cur.execute('INSERT INTO favorite_collection (query, ts) VALUES (?, ?)', (query, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def remove_favorite(query: str):
    # print('remove favorite?')
    conn = sqlite3.connect('stock_data.db')
    cur = conn.cursor()
    cur.execute('DELETE FROM favorite_collection WHERE query = ?', (query,))
    conn.commit()
    conn.close()

@callback(
    Output('sidebar-content', 'children', allow_duplicate=True),
    Input({'type': 'remove-favorite', 'index': ALL}, 'n_clicks'),
    State('sidebar-tabs', 'value'),
    prevent_initial_call=True
)
def remove_from_favorites(n_clicks_list, tab):
    ctx = callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_obj = ast.literal_eval(prop_id)
        idx = int(triggered_obj.get('index', 0))
    except Exception:
        raise dash.exceptions.PreventUpdate
    if not n_clicks_list or idx >= len(n_clicks_list) or n_clicks_list[idx] is None or n_clicks_list[idx] <= 0:
        raise dash.exceptions.PreventUpdate
    conn = sqlite3.connect('stock_data.db')
    try:
        df = pd.read_sql_query(f"SELECT query FROM favorite_collection ORDER BY id DESC LIMIT 20", conn)
        queries = [str(x) for x in df['query'].tolist()]
    except Exception:
        queries = []
    finally:
        conn.close()
    if idx < 0 or idx >= len(queries):
        raise dash.exceptions.PreventUpdate
    remove_favorite(queries[idx])
    if tab == 'favorite':
        return draw_favorite_panel()
    raise dash.exceptions.PreventUpdate

def get_sidebar_layout():
    return html.Div([
        dcc.Tabs(id='sidebar-tabs', value='recent', children=[
            dcc.Tab(label='Recent', value='recent'),
            dcc.Tab(label='Favorite', value='favorite'),
            dcc.Tab(label='Select', value='select'),
        ]),
        html.Div(id='sidebar-content', style={'overflowY': 'auto', 'maxHeight': '80vh', 'marginTop': '10px'}),
    ], style={'width': '300px', 'padding': '10px', 'borderRight': '1px solid #ddd'})

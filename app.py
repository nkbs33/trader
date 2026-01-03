from dash import Dash, html, dcc, callback, Output, Input, State
import dash
from dash.dependencies import ALL
import plotly.express as px
import pandas as pd
from plot import make_stock_figure
import sqlite3
from datetime import datetime
import ast

app = Dash()

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


def get_recent_queries(limit=10):
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
        btn = html.Button(label, id={'type': 'recent-query', 'index': i}, n_clicks=0, style={'width': '100%', 'textAlign': 'left', 'border': 'none', 'background': 'none', 'padding': '6px 0'})
        items.append(html.Li(btn))
    if not items:
        return html.Div("No recent queries yet.")
    return html.Ul(items)


def get_recent_queries_data(limit=10):
    conn = sqlite3.connect('stock_data.db')
    try:
        df = pd.read_sql_query(f"SELECT query FROM recent_queries ORDER BY id DESC LIMIT {limit}", conn)
        return [str(x) for x in df['query'].tolist()]
    except Exception:
        return []
    finally:
        conn.close()


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

def get_favorite_collection(limit=20):
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
    # print(items)
    return html.Ul(items)

# Sidebar with tabs
app.layout = html.Div([
    html.Div([
        dcc.Tabs(id='sidebar-tabs', value='recent', children=[
            dcc.Tab(label='Recent Queries', value='recent'),
            dcc.Tab(label='Favorite Collection', value='favorite'),
        ]),
        html.Div(id='sidebar-content', style={'overflowY': 'auto', 'maxHeight': '80vh', 'marginTop': '10px'}),
    ], style={'width': '300px', 'padding': '10px', 'borderRight': '1px solid #ddd'}),

    html.Div([
        html.H1(children='A股量化系统', style={'textAlign': 'center'}),
        dcc.Input(value='江西铜业', id='dropdown-selection', type='text', debounce=True, placeholder='输入股票名称或代码', style={'width': '320px'}),
        html.Button('Add to Favorites', id='add-favorite-btn', n_clicks=0, style={'marginLeft': '10px'}),
        dcc.Graph(id='graph-content')
    ], style={'flex': '1', 'padding': '10px'})
], style={'display': 'flex', 'height': '100vh'})



@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value'),
    Input('sidebar-tabs', 'value')
)
def update_graph(value, tab):
    if not value:
        return {}
    try:
        fig = make_stock_figure(value)
    except Exception as e:
        return {}
    return fig



# Sidebar tab content callback
@callback(
    Output('sidebar-content', 'children'),
    Input('sidebar-tabs', 'value')
)
def update_sidebar_content(tab):
    if tab == 'recent':
        return get_recent_queries()
    elif tab == 'favorite':
        return get_favorite_collection()
    return None

# Recent query click
@callback(
    Output('dropdown-selection', 'value', allow_duplicate=True),
    Output('sidebar-content', 'children', allow_duplicate=True),
    Input({'type': 'recent-query', 'index': ALL}, 'n_clicks'),
    State('sidebar-tabs', 'value'),
    prevent_initial_call=True,
)
def on_recent_click(n_clicks_list, tab):
    ctx = dash.callback_context
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
    
    if tab == 'favorite':
        return selected, get_favorite_collection()
    else:
        return selected, get_recent_queries()

# Favorite query click
@callback(
    Output('dropdown-selection', 'value', allow_duplicate=True),
    Input({'type': 'favorite-query', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def on_favorite_click(n_clicks_list):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_obj = ast.literal_eval(prop_id)
        idx = int(triggered_obj.get('index', 0))
    except Exception:
        raise dash.exceptions.PreventUpdate
    # get favorite queries
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

# Add to favorites button
@callback(
    Output('sidebar-content', 'children', allow_duplicate=True),
    Input('add-favorite-btn', 'n_clicks'),
    State('dropdown-selection', 'value'),
    State('sidebar-tabs', 'value'),
    prevent_initial_call=True
)
def add_to_favorites(n_clicks, value, tab):
    if n_clicks and value:
        add_favorite(value)
        # Always update sidebar content to reflect current tab
        if tab == 'favorite':
            return get_favorite_collection()
        elif tab == 'recent':
            return get_recent_queries()
    raise dash.exceptions.PreventUpdate

# Remove from favorites button
@callback(
    Output('sidebar-content', 'children', allow_duplicate=True),
    Input({'type': 'remove-favorite', 'index': ALL}, 'n_clicks'),
    State('sidebar-tabs', 'value'),
    prevent_initial_call=True
)
def remove_from_favorites(n_clicks_list, tab):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate
    prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
    try:
        triggered_obj = ast.literal_eval(prop_id)
        idx = int(triggered_obj.get('index', 0))
    except Exception:
        raise dash.exceptions.PreventUpdate
    # Only proceed if the clicked button's n_clicks is not None and > 0
    if not n_clicks_list or idx >= len(n_clicks_list) or n_clicks_list[idx] is None or n_clicks_list[idx] <= 0:
        raise dash.exceptions.PreventUpdate
    # get favorite queries
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
        return get_favorite_collection()
    raise dash.exceptions.PreventUpdate

if __name__ == '__main__':
    app.run(debug=True)

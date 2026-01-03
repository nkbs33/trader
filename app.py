from dash import Dash, html, dcc, callback, Output, Input
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


app.layout = html.Div([
    # sidebar and main content
    html.Div([
        html.H3('Recent Queries'),
        html.Div(id='recent-list', children=get_recent_queries(), style={'overflowY': 'auto', 'maxHeight': '80vh'})
    ], style={'width': '260px', 'padding': '10px', 'borderRight': '1px solid #ddd'}),

    html.Div([
        html.H1(children='A股量化系统', style={'textAlign': 'center'}),
        dcc.Input(value='江西铜业', id='dropdown-selection', type='text', debounce=True, placeholder='输入股票名称或代码', style={'width': '320px'}),
        dcc.Graph(id='graph-content')
    ], style={'flex': '1', 'padding': '10px'})
], style={'display': 'flex', 'height': '100vh'})


@callback(
    Output('graph-content', 'figure'),
    Output('recent-list', 'children'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    if not value:
        return {}, get_recent_queries()
    try:
        fig = make_stock_figure(value)
    except Exception as e:
        # on failure, return empty figure and current recent list
        return {}, get_recent_queries()

    # successful: record query and return updated list
    try:
        add_recent_query(value)
    except Exception:
        pass
    return fig, get_recent_queries()


@callback(
    Output('dropdown-selection', 'value'),
    Input({'type': 'recent-query', 'index': ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def on_recent_click(n_clicks_list):
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
    return selected

if __name__ == '__main__':
    app.run(debug=True)

from dash import Dash, html, dcc, callback, Output, Input
from webapp.ui.sidebar import get_sidebar_layout
from webapp.ui.plot import make_stock_figure
from webapp.db.stock_db import StockDatabase

app = Dash(suppress_callback_exceptions=True)

# Sidebar with tabs
app.layout = html.Div([
    # Inject global dark background for html and body
    get_sidebar_layout(),
    html.Div([
        # html.H1(children='A股量化系统', style={'textAlign': 'center', 'color': '#f5f5f5'}),
        dcc.Input(value='江西铜业', id='dropdown-selection', type='text', debounce=True, placeholder='输入股票名称或代码', style={'width': '320px', 'backgroundColor': '#222', 'color': '#f5f5f5', 'border': '1px solid #444'}),
        html.Button('Add to Favorites', id='add-favorite-btn', n_clicks=0, style={'marginLeft': '10px', 'backgroundColor': '#333', 'color': '#f5f5f5', 'border': '1px solid #444'}),
        dcc.Graph(id='graph-content'),
    ], style={'flex': '1', 'padding': '10px', 'backgroundColor': '#181818', 'color': '#f5f5f5'})
], style={'display': 'flex', 'height': '100vh', 'backgroundColor': '#111', 'color': '#f5f5f5'})

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

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "db":
        if len(sys.argv) < 3:
            print("provide db command")
            exit()
        db = StockDatabase()
        if sys.argv[2] == 'fetch':
            limit = None
            if len(sys.argv) > 3:
                try:
                    limit = int(sys.argv[3])
                except Exception:
                    print("Invalid limit, using all stocks.")
                    limit = None
            db.fetch_daily_data(limit=limit, sleep_sec=0.0)
        if sys.argv[2] == 'get-list':
            db.update_stock_info()
    elif cmd == "run":
        app.run(debug=True)


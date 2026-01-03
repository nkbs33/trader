from dash import Dash, html, dcc, callback, Output, Input
from webapp.ui.sidebar import get_sidebar_layout
from webapp.ui.plot import make_stock_figure

app = Dash()

# Sidebar with tabs
app.layout = html.Div([
    get_sidebar_layout(),
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

if __name__ == '__main__':
    app.run(debug=True)

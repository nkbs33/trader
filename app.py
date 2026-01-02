from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd
from plot import make_stock_figure

#df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash()

app.layout = [
    html.H1(children='A股量化系统', style={'textAlign':'center'}),
    dcc.Dropdown(['江西铜业','中芯国际'], '江西铜业', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
]

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)

def update_graph(value):
    return make_stock_figure(value)

if __name__ == '__main__':
    app.run(debug=True)

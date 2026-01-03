import dash
from dash import html, dcc, callback, Output, Input, State, callback_context
from dash.dependencies import ALL
import ast
import sqlite3
import pandas as pd
from datetime import datetime
from webapp.ui.favorite_panel import draw_favorite_panel
from webapp.ui.recent_panel import draw_recent_panel

@callback(
    Output('sidebar-content', 'children'),
    Input('sidebar-tabs', 'value')
)
def on_tab_clicked(tab):
    if tab == 'recent':
        return draw_recent_panel()
    elif tab == 'favorite':
        return draw_favorite_panel()
    return None


def get_sidebar_layout():
    return html.Div([
        dcc.Tabs(id='sidebar-tabs', value='recent', children=[
            dcc.Tab(label='Recent', value='recent'),
            dcc.Tab(label='Favorite', value='favorite'),
            dcc.Tab(label='Pick', value='pick'),
        ]),
        html.Div(id='sidebar-content', style={'overflowY': 'auto', 'maxHeight': '80vh', 'marginTop': '10px'}),
    ], style={'width': '300px', 'padding': '10px', 'borderRight': '1px solid #ddd'})

import dash
from dash import html, dcc, callback, Output, Input, State, callback_context
from dash.dependencies import ALL
import ast
import sqlite3
import pandas as pd
from datetime import datetime
from webapp.ui.favorite_panel import draw_favorite_panel
from webapp.ui.recent_panel import draw_recent_panel
from webapp.ui.analyze_panel import draw_analyze_panel


@callback(
    Output('sidebar-content', 'children'),
    Input('sidebar-tabs', 'value')
)
def on_tab_clicked(tab):
    if tab == 'recent':
        return draw_recent_panel()
    elif tab == 'favorite':
        return draw_favorite_panel()
    elif tab == 'analyze':
        return draw_analyze_panel()
    return None


def get_sidebar_layout():
    return html.Div([
        dcc.Tabs(
            id='sidebar-tabs', value='recent',
            children=[
                dcc.Tab(label='最近', value='recent', style={'backgroundColor': '#222', 'color': '#f5f5f5', 'border': 'none'}, selected_style={'backgroundColor': '#333', 'color': '#FFD700'}),
                dcc.Tab(label='收藏', value='favorite', style={'backgroundColor': '#222', 'color': '#f5f5f5', 'border': 'none'}, selected_style={'backgroundColor': '#333', 'color': '#FFD700'}),
                dcc.Tab(label='分析', value='analyze', style={'backgroundColor': '#222', 'color': '#f5f5f5', 'border': 'none'}, selected_style={'backgroundColor': '#333', 'color': '#FFD700'}),
            ],
            style={'backgroundColor': '#181818', 'color': '#f5f5f5'}
        ),
        html.Div(id='sidebar-content', style={'overflowY': 'auto', 'maxHeight': '80vh', 'marginTop': '10px', 'backgroundColor': '#181818', 'color': '#f5f5f5'}),
    ], style={'width': '300px', 'padding': '10px', 'borderRight': '1px solid #333', 'backgroundColor': '#181818', 'color': '#f5f5f5'})

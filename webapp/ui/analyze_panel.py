import dash
from dash import html, dcc, callback, Output, Input, State
from dash.dependencies import ALL
import ast
import sqlite3
import pandas as pd
from datetime import datetime
from webapp.db.stock_db import StockDatabase
from webapp.ui.plot import calculate_kdj, double_line

def draw_analyze_panel():
    return html.Div([
        html.Button('分析主图数据', id='analyze-btn', n_clicks=0, style={'marginBottom': '10px', 'background': '#222', 'color': '#f5f5f5', 'border': '1px solid #444'}),
        dcc.Textarea(
            id='analyze-result',
            value='',
            style={'width': '90%', 'height': 400, 'background': '#181818', 'color': '#f5f5f5', 'border': '1px solid #444', 'padding': '8px', 'borderRadius': '6px'},
            readOnly=True
        )
    ], style={'background': '#181818', 'color': '#f5f5f5', 'padding': '10px', 'borderRadius': '8px'})


def analyze_df(df):
    df = calculate_kdj(df)
    df = double_line(df)
    df = df.tail(60)

    result = []
    for i in range(1, len(df)):
        if df.iloc[i]['成交量'] >= 2 * df.iloc[i - 1]['成交量']:
            date = df.iloc[i]['日期'].strftime('%Y年%m月%d日')
            result.append(f"{date}")
    if result:
        result_str = "倍量柱:\n" + "\n".join(result) + "\n存在倍量柱，值得关注\n" 
    else:
        result_str = "没有倍量柱\n"

    j = df.iloc[-1]['J']
    result_str += "当前的J值:\n" + f"{j:.2f}" +'\n'
    if j > 80:
        result_str += '属于相对高位\n'
    elif j < 12:
        result_str += '属于相对低位\n'
    else:
        result_str += '属于相对中部位置\m'
    return result_str

@callback(
    Output('analyze-result', 'value'),
    Input('analyze-btn', 'n_clicks'),
    State('dropdown-selection', 'value'),
    prevent_initial_call=True,
)
def analyze_main_chart(n_clicks, stock_name):
    if not stock_name:
        return '未选择股票'
    try:
        db = StockDatabase()
        df = db.query_daily_data(stock_name, day_count=180)
        if df.empty:
            return f"未找到 {stock_name} 的数据"
        # 这里只显示前5行和列名作为占位符
        return analyze_df(df)
    

    except Exception as e:
        return f"分析出错: {e}"


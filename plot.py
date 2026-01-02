import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calculate_kdj(df:pd.DataFrame, n=9, m1=3, m2=3):
    low_list = df['最低'].rolling(window=n).min()
    high_list = df['最高'].rolling(window=n).max()
    rsv = (df['收盘']-low_list)/(high_list-low_list)*100

    df['K'] = rsv.ewm(com=m1-1, adjust=False).mean()
    df['D'] = df['K'].ewm(com=m2-1, adjust=False).mean()
    df['J'] = 3 * df['K'] - 2 * df['D']
    return df


def make_stock_figure(table_name):
    conn = sqlite3.connect("stock_data.db")
    query = f"""
        SELECT * FROM {table_name}
        ORDER BY 日期 DESC
        LIMIT 180
    """
    df = pd.read_sql(query, conn)
    conn.close()

    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期")

    df = df[["日期","开盘", "最高", "最低", "收盘", "成交量"]]
    df['MA10'] = df['收盘'].rolling(window=10).mean()
    df = calculate_kdj(df)

    df['Date_Str'] = df['日期'].dt.strftime('%Y-%m-%d')

    fig = make_subplots(rows=3, cols=1,
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        subplot_titles=(f'{table_name}', 'Volume', 'KDJ'),
                        row_width=[0.3, 0.2, 0.5])
    
    # Row 1 K Line
    fig.add_trace(go.Candlestick(
        x=df['Date_Str'],
        open=df['开盘'], high=df['最高'],
        low=df['最低'], close=df['收盘'],
        name='K-Line',
        increasing_line_color='red', increasing_fillcolor='red',
        decreasing_line_color='green', decreasing_fillcolor='green'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df['Date_Str'], y=df['MA10'], 
        line=dict(color='blue', width=1), 
        name='MA10'
    ), row=1, col=1)
    
    # Row 2 Volume
    fig.add_trace(go.Bar(
        x=df['Date_Str'], y=df['成交量'], 
        marker_color='orange', 
        name='Volume'
    ), row=2, col=1)

    # Row 3 KDJ
    fig.add_trace(go.Scatter(x=df['Date_Str'], y=df['K'], line=dict(color='black', width=1), name='K'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date_Str'], y=df['D'], line=dict(color='orange', width=1), name='D'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date_Str'], y=df['J'], line=dict(color='purple', width=1), name='J'), row=3, col=1)

    fig.add_hline(y=80, line_dash="dot", line_color="red", row=3, col=1)
    fig.add_hline(y=13, line_dash="dot", line_color="green", row=3, col=1)

    fig.update_layout(
        #title=f'Interactive Analysis: {table_name}',
        xaxis_rangeslider_visible=False,
        height=1000,
        template='plotly',
    )
    fig.update_xaxes(type='category',showticklabels=False)
    fig.update_xaxes(rangeslider_visible=False, row=2, col=1)
    fig.update_xaxes(rangeslider_visible=True, row=3, col=1)   

    return fig

def plot_interactive_stock():
    fg = make_stock_figure("江西铜业")
    fg.show()

#plot_interactive_stock()
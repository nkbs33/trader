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

def double_line(df:pd.DataFrame):
    short = df['收盘'].ewm(span=10).mean()
    short = short.ewm(span=10).mean()
    df['short'] = short
    long = (df['收盘'].ewm(span=14).mean() + df['收盘'].ewm(span=28).mean()
            + df['收盘'].ewm(span=57).mean() + df['收盘'].ewm(span=114).mean())*0.25
    df['long'] = long
    return df


def make_stock_figure(stock, day_count=60):
    conn = sqlite3.connect("stock_data.db")
    query = f"""
        SELECT 日期, 开盘, 最高, 最低, 收盘, 成交量, 涨跌幅, 振幅 FROM daily_data
        WHERE stock = ?
        ORDER BY 日期 DESC
        LIMIT ?
    """
    df = pd.read_sql(query, conn, params=(stock, day_count+120))
    conn.close()

    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期")

    # df['MA10'] = df['收盘'].rolling(window=10).mean()
    df = calculate_kdj(df)
    df = double_line(df)

    df = df.tail(day_count)

    df['Date_Str'] = df['日期'].dt.strftime('%Y-%m-%d')

    fig = make_subplots(rows=3, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.03,
                        row_width=[0.3, 0.2, 0.5])

    # Row 1 K Line
    # Add custom hovertemplate to show 涨跌幅
    hovertemplate = (
        '日期: %{x}<br>' +
        '开盘: %{open}<br>' +
        '最高: %{high}<br>' +
        '最低: %{low}<br>' +
        '收盘: %{close}<br>' +
        '涨跌幅: %{customdata[0]:.2f}%<br>'+
        '振幅: %{customdata[1]:.2f}%'
    )
    fig.add_trace(go.Candlestick(
        x=df['Date_Str'],
        open=df['开盘'], high=df['最高'],
        low=df['最低'], close=df['收盘'],
        name='K-Line',
        increasing_line_color='red', increasing_fillcolor='red',
        decreasing_line_color='green', decreasing_fillcolor='green',
        customdata=list(zip(df['涨跌幅'], df['振幅'])),
        hovertemplate=hovertemplate
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df['Date_Str'], y=df['short'],
        line=dict(color='white', width=1),
        name='短线'
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df['Date_Str'], y=df['long'],
        line=dict(color='#D4A135', width=1),
        name='主力'
    ), row=1, col=1)

    # Row 2 Volume
    vol_colors = ['red' if c >= o else 'green' for c, o in zip(df['收盘'], df['开盘'])]
    fig.add_trace(go.Bar(
        x=df['Date_Str'], y=df['成交量'],
        marker_color=vol_colors,
        name='Volume',
        showlegend=False,
    ), row=2, col=1)

    # Mark high volume days (volume > 2x previous day)
    df['prev_volume'] = df['成交量'].shift(1)
    high_vol_mask = df['成交量'] > 2 * df['prev_volume']
    high_vol_dates = df.loc[high_vol_mask, 'Date_Str']
    high_vol_values = df.loc[high_vol_mask, '成交量']
    fig.add_trace(go.Scatter(
        x=high_vol_dates,
        y=high_vol_values,
        mode='markers',
        marker=dict(symbol='star', color='gold', size=12, line=dict(width=1, color='black')),
        name='High Volume',
        showlegend=True
    ), row=2, col=1)

    # Row 3 KDJ
    fig.add_trace(go.Scatter(x=df['Date_Str'], y=df['K'], line=dict(color='black', width=1), name='K'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date_Str'], y=df['D'], line=dict(color='orange', width=1), name='D'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date_Str'], y=df['J'], line=dict(color='purple', width=1), name='J'), row=3, col=1)

    fig.add_hline(y=80, line_dash="dot", line_color="red", row=3, col=1)
    fig.add_hline(y=13, line_dash="dot", line_color="green", row=3, col=1)

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=1000,
        width=800,
        template='plotly_dark',
        paper_bgcolor='#222222',
        plot_bgcolor='#222222',
        xaxis=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikecolor='rgba(0,0,0,0.5)',
            spikedash='solid',
        ),
        xaxis2=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikecolor='rgba(0,0,0,0.5)',
            spikedash='solid',
        ),
        xaxis3=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikecolor='rgba(0,0,0,0.5)',
            spikedash='solid',
        ),
        yaxis=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikecolor='rgba(0,0,0,0.5)',
            spikedash='solid',
        ),
        yaxis2=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikecolor='rgba(0,0,0,0.5)',
            spikedash='solid',
        ),
        yaxis3=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikethickness=1,
            spikecolor='rgba(0,0,0,0.5)',
            spikedash='solid',
        ),
        hovermode='x',
    )
    fig.update_xaxes(type='category', showticklabels=False)

    return fig

def plot_interactive_stock():
    fg = make_stock_figure("江西铜业")
    fg.show()

#plot_interactive_stock()
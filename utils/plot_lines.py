import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jenkspy import JenksNaturalBreaks
from plotly.subplots import make_subplots
from utils.commissions import ForexCommission
from utils.testcases import slides_generator
from utils.constants import *
from utils.psql import PSQLData
from utils.strategies import BuyAndHold, RSIPositionSizing
import argparse
import backtrader as bt
import itertools
import pandas as pd
import pickle
import plotly.express as px
import plotly.graph_objects as go
import random


def parse_args():
    parser = argparse.ArgumentParser(description='Super MA Backtest')

    parser.add_argument('--cluster', '-c', action='store_true', required=False, help='Plot clusters')
    parser.add_argument('--line', '-l', action='store_true', required=False, help='Plot lines')
    parser.add_argument('--trades', '-t', action='store_true', required=False, help='Plot Trades and Cash')
    parser.add_argument('--slidingwindow', '-w', action='store_true', required=False, help='Plot Sliding Window')
    parser.add_argument('--subplot', '-s', action='store_true', required=False, help='Subplots')
    parser.add_argument('--subplotwindows', '-sw', action='store_true', required=False, help='Subplots for Sliding Window')
    parser.add_argument('--filenames', '-f', nargs='+', default=[], required=True, help='Filenames of csv')
    parser.add_argument('--zero', '-z', action='store_true', required=False, help='Keep 0 rtot')

    return parser.parse_args()


def create_clusters_and_plot(filepath, zero_rtot):
    df = pd.read_csv(filepath)

    number_of_clusters = 3

    jnb = JenksNaturalBreaks(nb_class=number_of_clusters)

    jnb.fit(df['returns_rtot'].tolist())

    legends = jnb.inner_breaks_
    cluster = pd.DataFrame({'cluster': jnb.labels_})

    df['cluster'] = cluster
    df.to_csv(filepath, index=False)

    df = df.sort_values('cluster')

    if not zero_rtot:
        df = df.loc[df['returns_rtot'] != 0]

    headers = [header for header in df.columns.values.tolist() if 'ma_period' in header]
    random.shuffle(headers)

    clusters = [df.loc[df['cluster'] == i] for i in range(number_of_clusters)]

    fig = px.scatter_3d(df, x=headers[0], y=headers[1], z=headers[2],
                        range_x=[df[headers[0]].min(), df[headers[0]].max()],
                        range_y=[df[headers[1]].min(), df[headers[1]].max()],
                        range_z=[df[headers[2]].min(), df[headers[2]].max()],
                        color='returns_rtot',
                        color_continuous_scale=[(0.00, 'rgba(255, 0, 0, 1)'), (0.50, 'rgba(255, 255, 255, 1)'),
                                                (0.50, 'rgba(255, 255, 255, 1)'), (1.00, 'rgba(0, 255, 0, 1)')],
                        range_color=(-df['returns_rtot'].abs().max(), df['returns_rtot'].abs().max()),
                        symbol='cluster',
                        hover_data=[*headers, 'returns_rtot', 'cluster'],
                        )

    for i, cluster in enumerate(clusters):
        if i == 0:
            name = f'<={legends[i]:.2f}'
        elif i == len(clusters) - 1:
            name = f'>{legends[-1]:.2f}'
        else:
            name = f'<{legends[i - 1]:.2f}< rtot <= {legends[i]:.2f}'

        fig.add_mesh3d(x=cluster[headers[0]], y=cluster[headers[1]], z=cluster[headers[2]],
                       alphahull=0,
                       name=name,
                       opacity=.1,
                       showlegend=True,
                       showscale=True,
                       hoverinfo='none',
                       visible='legendonly',
                       )

    fig.update_layout(title='Interactive Cluster Shapes in 3D',
                      scene=dict(aspectmode='cube',
                                 xaxis=dict(zeroline=True, title=f'x: {headers[0]}', range=[df[headers[0]].min(), df[headers[0]].max()], autorange='reversed'),
                                 yaxis=dict(zeroline=True, title=f'y: {headers[1]}', range=[df[headers[1]].min(), df[headers[1]].max()], autorange='reversed'),
                                 zaxis=dict(zeroline=True, title=f'z: {headers[2]}', range=[df[headers[2]].min(), df[headers[2]].max()],),),
                      coloraxis_colorbar=dict(yanchor="top", y=1, x=0, ticks='outside', ticksuffix=''),
                      )

    fig.show()


def plot_lines(filepath, zero_rtot):
    df = pd.read_csv(filepath)

    headers = [header for header in df.columns.values.tolist() if 'period' in header]
    random.shuffle(headers)

    if not zero_rtot:
        df = df.loc[df['returns_rtot'] != 0]

    df = df.sort_values(headers[0])

    x = df[headers[0]]
    y = df['returns_rtot']
    y2 = df['drawdown_max_drawdown']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, name='returns_rtot'))
    fig.add_trace(go.Scatter(x=x, y=y2, name='drawdown_max_drawdown', yaxis='y2'))

    fig.update_layout(
        xaxis=dict(title=headers[0], domain=[0.2, 0.8]),
        yaxis=dict(title='returns_rtot'),
        yaxis2=dict(title='drawdown_max_drawdown', anchor='free', overlaying='y', side='left', position=0.15),
    )

    fig.update_layout(
        title_text='',
    )

    fig.show()


def subplot_lines(filepath, zero_rtot):
    df = pd.read_csv(filepath)

    if not zero_rtot:
        df = df.loc[df['returns_rtot'] != 0]

    headers = ['lower_ma_period',
               'upper_ma_period',
               'wave_ma_period',
               #    'killer_ma_period',
               #    'enter_ma_period',
               ]

    axis_pairs = itertools.combinations(headers, 2)

    plots = []

    for axis_pair in axis_pairs:
        # add returns_rtot the 3rd axis as color
        plots.append(list(axis_pair) + ['returns_rtot'])

    subplot_titles = [f'y:{plot[1]} - x:{plot[0]}' for plot in plots]

    fig = make_subplots(rows=1, cols=len(subplot_titles), start_cell='bottom-left', subplot_titles=subplot_titles)

    for i, plot in enumerate(plots, 1):
        fig['layout'][f'xaxis{i}']['title'] = plot[0]
        fig['layout'][f'yaxis{i}']['title'] = plot[1]

    for plot in plots:
        plot[0], plot[1], plot[2] = df[plot[0]], df[plot[1]], df[plot[2]]

    colorscale = [(0.00, 'rgba(255, 255, 255, 1)'), (1.00, 'rgba(0, 255, 0, 1)')]

    def marker_maker(df, color, color_header='returns_rtot'):
        cmin = 0
        cmax = df[color_header].max()
        colorscale = [(0.00, 'rgba(255, 255, 255, 1)'), (1.00, 'rgba(0, 255, 0, 1)')]
        colorbar = dict(title='rtot', yanchor="top", y=1, x=-0.1, ticks='outside', ticksuffix='')

        return dict(cmin=cmin,
                    cmax=cmax,
                    colorscale=colorscale,
                    color=color,
                    colorbar=colorbar,
                    )

    for i, plot in enumerate(plots, 1):
        fig.add_trace(go.Scatter(x=plot[0], y=plot[1], mode='markers', marker=marker_maker(df, plot[2])), row=1, col=i)

    fig.show()


def plot_window(filepath, zero_rtot):
    df = pd.read_csv(filepath)
    header = 'datetime_before'

    if not zero_rtot:
        df = df.loc[df['returns_rtot'] != 0]

    x = df[header]
    y = df['returns_rtot']
    y2 = df['drawdown_max_drawdown']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, name='returns_rtot'))
    fig.add_trace(go.Scatter(x=x, y=y2, name='drawdown_max_drawdown', yaxis='y2'))

    fig.update_layout(
        xaxis=dict(title=header, dtick='M1', tickformat='%b\n%Y'),
        yaxis=dict(title='returns_rtot'),
        yaxis2=dict(title='drawdown_max_drawdown', anchor='free', overlaying='y', side='left', position=0.15),
    )

    fig.update_layout(
        title_text='',
    )

    fig.show()


def subplot_windows(filepaths, zero_rtot):

    dfs = []
    for filepath in filepaths:
        df = pd.read_csv(filepath)
        if not zero_rtot:
            df = df.loc[df['returns_rtot'] != 0]
        dfs.append(df)

    headers = [os.path.split(filepath)[-1] for filepath in filepaths]
    plots = []

    for header in headers:
        # add returns_rtot the 3rd axis as color
        plots.append(['datetime_before', 'returns_rtot', 'drawdown_moneydown'] + [header])

    subplot_titles = [f'{plot[-1]}' for plot in plots]

    fig = make_subplots(rows=len(subplot_titles), cols=1, start_cell='bottom-left',
                        subplot_titles=subplot_titles,
                        specs=[[{'secondary_y': True}] for _ in range(len(subplot_titles))],
                        vertical_spacing=0.05
                        )

    for df, plot in zip(dfs, plots):
        plot[0], plot[1], plot[2] = df[plot[0]], df[plot[1]], df[plot[2]]

    for i, plot in enumerate(plots, 1):
        fig.add_trace(go.Scatter(x=plot[0], y=plot[1], name=f'{plot[-1]}_rtot', mode='lines+markers'), row=i, col=1, secondary_y=False)
        fig.add_trace(go.Scatter(x=plot[0], y=plot[2], name=f'{plot[-1]}_mdd', mode='lines+markers', line=dict(dash='dash')), row=i, col=1, secondary_y=True)

    fig.show()


def plot_trades(filepath):
    strats = pickle.load(open(filepath, 'rb'))

    timeline = [bt.num2date(time_in_float) for time_in_float in strats.array]
    cash_line = strats.stats.broker.array
    trade_line_pos = strats.stats.trades.lines.pnlplus.array
    trade_line_neg = strats.stats.trades.lines.pnlminus.array

    data_dict = {
        'time': timeline,
        'cash': cash_line,
        'trade_line_pos': trade_line_pos,
        'trade_line_neg': trade_line_neg,
    }

    df = pd.DataFrame(data_dict)

    x = df['time']
    y = df['cash']
    y2 = df['trade_line_pos']
    y3 = df['trade_line_neg']

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, name='cash'))
    fig.add_trace(go.Scatter(x=x, y=y2, name='trade_line_pos', yaxis='y2', mode='markers'))
    fig.add_trace(go.Scatter(x=x, y=y3, name='trade_line_neg', yaxis='y2', mode='markers'))

    fig.update_layout(
        xaxis=dict(title='time', domain=[0.2, 0.8]),
        yaxis=dict(title='cash'),
        yaxis2=dict(title='trade', anchor='free', overlaying='y', side='left', position=0.15),
    )

    fig.update_layout(
        title_text='',
    )

    fig.show()


if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)

    args = parse_args()

    filepaths = [os.path.join(script_dir, filename) for filename in args.filenames]

    if args.cluster:
        create_clusters_and_plot(filepaths[0], args.zero)
    elif args.line:
        plot_lines(filepaths[0], args.zero)
    elif args.subplot:
        subplot_lines(filepaths[0], args.zero)
    elif args.slidingwindow:
        plot_window(filepaths[0], args.zero)
    elif args.subplotwindows:
        subplot_windows(filepaths, args.zero)
    elif args.trades:
        plot_trades(filepaths[0])

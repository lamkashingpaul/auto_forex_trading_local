from backtrader_plotly.plotter import BacktraderPlotly
from backtrader_plotly.scheme import PlotScheme
from jenkspy import JenksNaturalBreaks
from plotly.subplots import make_subplots
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io

colorscale = [(0.00, 'rgba(255, 0, 0, 1)'), (0.50, 'rgba(255, 255, 255, 1)'),
              (0.50, 'rgba(255, 255, 255, 1)'), (1.00, 'rgba(0, 255, 0, 1)')]


def plot_backtest_result(cerebro, output='', show=False):
    # define plot scheme with new additional scheme arguments
    scheme = PlotScheme(decimal_places=5, max_legend_text_width=16)

    # plot and save figures as `plotly` graph object
    figs = cerebro.plot(BacktraderPlotly(show=show, scheme=scheme))

    figs = [x for fig in figs for x in fig]  # flatten output

    for i, fig in enumerate(figs):
        if show:
            plotly.io.to_html(fig, full_html=False)  # open html in the browser

        if output:
            file = os.path.join(output, f'{i}.html')
            plotly.io.write_html(fig, file=file)  # save the html file

    return figs


def marker_maker(df, color, color_header='returns_rtot'):
    cmax = df[color_header].abs().max()
    cmin = -cmax
    colorscale = [(0.00, 'rgba(255, 0, 0, 1)'), (0.50, 'rgba(255, 255, 255, 1)'),
                  (0.50, 'rgba(255, 255, 255, 1)'), (1.00, 'rgba(0, 255, 0, 1)')]

    colorbar = dict(title='rtot', yanchor="top", y=1, x=-0.1, ticks='outside', ticksuffix='')

    return dict(cmin=cmin,
                cmax=cmax,
                colorscale=colorscale,
                color=color,
                colorbar=colorbar,
                )


def plot_2d_heatmap(x, y, z, input, output, group_by=True, keep_zero_rtot=False, show=False):
    df = pd.read_csv(input)

    if not keep_zero_rtot:
        df = df.loc[df['returns_rtot'] != 0]

    if group_by:
        df = df.groupby([x, y], as_index=False)[z].mean()

    fig = go.Figure(data=go.Heatmap(x=df[x].to_list(), y=df[y].to_list(), z=df[z].to_list(),
                                    zmid=0, colorscale=colorscale,
                                    ))

    fig.update_layout(title='2D Heatmap', xaxis_title=x, yaxis_title=y,)

    if show:
        fig.show()

    fig.write_html(file=f'{output}_plot_2d_heatmap.html')


def plot_3d_heatmap_with_cluster(x, y, z, w, input, output, num_of_clusters=3, keep_zero_rtot=False, show=False):
    df = pd.read_csv(input)
    jnb = JenksNaturalBreaks(nb_class=num_of_clusters)

    jnb.fit(df[w].tolist())

    legends = jnb.inner_breaks_
    cluster = pd.DataFrame({'cluster': jnb.labels_})

    df['cluster'] = cluster
    df.to_csv(input, index=False)

    df = df.sort_values('cluster')

    if not keep_zero_rtot:
        df = df.loc[df['returns_rtot'] != 0]

    headers = [x, y, z]
    clusters = [df.loc[df['cluster'] == i] for i in range(num_of_clusters)]

    fig = px.scatter_3d(df, x=x, y=y, z=z,
                        range_x=[df[x].min(), df[x].max()],
                        range_y=[df[y].min(), df[y].max()],
                        range_z=[df[z].min(), df[z].max()],
                        color=w,
                        color_continuous_scale=[(0.00, 'rgba(255, 0, 0, 1)'), (0.50, 'rgba(255, 255, 255, 1)'),
                                                (0.50, 'rgba(255, 255, 255, 1)'), (1.00, 'rgba(0, 255, 0, 1)')],
                        range_color=(-df[w].abs().max(), df[w].abs().max()),
                        symbol='cluster',
                        hover_data=[*headers, w, 'cluster'],
                        )

    for i, cluster in enumerate(clusters):
        if i == 0:
            name = f'<={legends[i]:.2f}'
        elif i == len(clusters) - 1:
            name = f'>{legends[-1]:.2f}'
        else:
            name = f'<{legends[i - 1]:.2f}< rtot <= {legends[i]:.2f}'

        fig.add_mesh3d(x=cluster[x], y=cluster[y], z=cluster[z],
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
                                 xaxis=dict(zeroline=True, title=f'x: {x}', range=[df[x].min(), df[x].max()], autorange='reversed'),
                                 yaxis=dict(zeroline=True, title=f'y: {y}', range=[df[y].min(), df[y].max()], autorange='reversed'),
                                 zaxis=dict(zeroline=True, title=f'z: {z}', range=[df[z].min(), df[z].max()],),),
                      coloraxis_colorbar=dict(yanchor="top", y=1, x=0, ticks='outside', ticksuffix=''),
                      )

    if show:
        fig.show()

    fig.write_html(file=f'{output}_plot_3d_heatmap_with_cluster.html')


def plot_sliding_comparison(price, inputs, output, keep_zero_rtot=False, show=False):
    correlation = df = pd.read_csv(price)

    x = 'datetime_before'
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Scatter(x=df['Datetime'], y=df['Close'], name='Close Price', fill='tozeroy'), secondary_y=True)

    strategy_names = []

    for input in inputs:
        df = pd.read_csv(input)

        if not keep_zero_rtot:
            df = df.loc[df['returns_rtot'] != 0]

        fig.add_trace(go.Scatter(x=df[x], y=df['returns_rtot'], mode='lines', name=input,))

        strategy_name = input.split('/')[-2]
        strategy_names.append(strategy_name)

        df = df.rename(columns={'datetime_before': 'Datetime', 'returns_rtot': f'{strategy_name}_returns_rtot'})

        correlation = correlation.merge(df[['Datetime', f'{strategy_name}_returns_rtot']], how='right', on='Datetime')
        correlation = correlation.fillna(method='ffill')

    for price_name in ['Close', 'Open', 'High', 'Low']:
        correlation[[price_name] + [f'{strategy_name}_returns_rtot' for strategy_name in strategy_names]].corr().to_csv(f'{output}_{price_name}_correlation.csv')

    if show:
        fig.show()

    fig.write_html(file=f'{output}_plot_sliding_comparison.html')

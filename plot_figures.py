from plotly.subplots import make_subplots
import argparse
import itertools
import os
import pandas as pd
import plotly.graph_objects as go


def parse_args():
    parser = argparse.ArgumentParser(description='Plot Comparison')

    parser.add_argument('--filename', '-f', default=None, required=True, help='Filename of csv')
    parser.add_argument('--zero', '-z', action='store_true', required=False, help='Keep 0 rtot')
    parser.add_argument('--comparison', '-c', action='store_true', required=False, help='Plot comparison')

    return parser.parse_args()


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


def plot_comparison(filepath, keep_zero_rtot):
    df = pd.read_csv(filepath)
    strengths = df['strength'].unique().tolist()

    if not keep_zero_rtot:
        df = df.loc[df['returns_rtot'] != 0]

    headers = ['slow_ma_period', 'fast_ma_period', 'returns_rtot']

    use_strengths = (True, False)
    plots = [list(item) for item in itertools.product(strengths, use_strengths)]
    subplot_titles = [f'Strength = {strength}, Use = {use_strength} ' for strength, use_strength in plots]

    cols = len(use_strengths)
    rows = len(strengths)

    fig = make_subplots(rows=rows, cols=cols, start_cell='bottom-left', subplot_titles=subplot_titles,
                        horizontal_spacing=0.05, vertical_spacing=0.10)

    xmax = df[headers[0]].max()
    xmin = df[headers[0]].min()
    ymax = df[headers[1]].max()
    ymin = df[headers[1]].min()

    for i, plot in enumerate(plots, 1):
        fig['layout'][f'xaxis{i}']['title'] = headers[0]
        fig['layout'][f'yaxis{i}']['title'] = headers[1]
        fig['layout'][f'yaxis{i}']['range'] = [xmin, xmax]
        fig['layout'][f'yaxis{i}']['range'] = [ymin, ymax]

    for i, (strength, use_strength) in enumerate(plots):
        strength = df.loc[(df['strength'] == strength) & (df['use_strength'] == use_strength)]
        # collect x, y, z axis of plot
        plots[i] = [strength[headers[0]], strength[headers[1]], strength[headers[2]]]

    colorscale = [(0.00, 'rgba(255, 0, 0, 1)'), (0.50, 'rgba(255, 255, 255, 1)'),
                  (0.50, 'rgba(255, 255, 255, 1)'), (1.00, 'rgba(0, 255, 0, 1)')]

    zmax = df[headers[2]].abs().max()
    zmin = -zmax

    for i, plot in enumerate(plots):
        fig.add_trace(go.Heatmap(x=plot[0], y=plot[1], z=plot[2], zmax=zmax, zmin=zmin,
                                 colorscale=colorscale), row=(i // cols) + 1, col=(i % cols) + 1)

    fig.show()


if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)

    args = parse_args()
    filepath = os.path.join(script_dir, args.filename)

    if args.comparison:
        plot_comparison(filepath, args.zero)

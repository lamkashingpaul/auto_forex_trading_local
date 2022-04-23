from pathlib import Path
import argparse
import os
import pandas as pd
import plotly.graph_objects as go
import sys


def get_parser():
    parser = argparse.ArgumentParser(description='Plot Loss Curve')

    # load trained model
    parser.add_argument('--log', '-l', dest='log',
                        default='', required=False,
                        help='input training log', metavar='FILE')

    return parser


def main():
    args = get_parser().parse_args()

    log = os.path.abspath(args.log)
    log = Path(log)

    df = pd.read_csv(log)

    x = df['epoch']
    train_loss = df['loss']
    val_loss = df['val_loss']

    fig = go.Figure()
    fig.add_trace(go.Scatter(name='train_loss', x=x, y=train_loss, mode='lines'))
    fig.add_trace(go.Scatter(name='val_loss', x=x, y=val_loss, mode='lines'))

    fig.write_html(file=f'{log}_loss_plot.html')


if __name__ == '__main__':
    # plot_training_history.py --log ./reports/16_lstm_price_prediction_model/hour_bar_predict_1_bar_training_lr_0.001_training.log
    # plot_training_history.py --log ./reports/16_lstm_price_prediction_model/hour_bar_predict_1_bar_training_lr_0.005_training.log
    # plot_training_history.py --log ./reports/16_lstm_price_prediction_model/hour_bar_predict_10_bar_training_lr_0.005_training.log
    main()

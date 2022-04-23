from datetime import date, datetime
from pathlib import Path
from utils.commissions import ForexCommission
from utils.constants import PERIODS, SYMBOLS
from utils.datafeeds import DownloadedCSVData, PSQLData
import argparse
import backtrader as bt
import os
import sys


def get_default_parser(description='Backtest Basic'):
    parser = argparse.ArgumentParser(description=description)

    # load trained model
    parser.add_argument('--model', '-m', dest='model',
                        default='', required=False,
                        help='input trained model', metavar='FILE')

    parser.add_argument('--scaler', '-sc', dest='scaler',
                        default='', required=False,
                        help='input scaler for model', metavar='FILE')

    parser.add_argument('--align', '-a', action='store_true',
                        required=False, help='align future prediction to today')

    # arguments for backtest data from local csv files
    parser.add_argument('--csv', '-c', nargs='+', default=[],
                        required=False, help='input csv files', metavar='FILE')

    # arguments for getting price data from local csv file
    parser.add_argument('--dataname', '-d', dest='dataname',
                        default='', required=False,
                        help='input price data csv file', metavar='FILE')

    # arguments for getting price data from local csv file
    parser.add_argument('--prediction', '-pred', dest='prediction',
                        type=int, default=-1, required=False,
                        help='data column index for prediction')

    # arguments for getting data from PostgreSQL
    parser.add_argument('--symbol', '-s', choices=SYMBOLS,
                        default='EURUSD', required=False,
                        help='symbols to be traded.')

    parser.add_argument('--period', '-p', choices=PERIODS.keys(),
                        default='H1', required=False,
                        help='timeframe period to be traded.')

    parser.add_argument('--fromdate', '-from', type=date.fromisoformat,
                        default=date(2021, 1, 1),
                        required=False, help='date starting the trade.')

    parser.add_argument('--todate', '-to', type=date.fromisoformat,
                        default=date(2022, 1, 1),
                        required=False, help='date ending the trade.')

    parser.add_argument('--optimization', '-o', action='store_true',
                        required=False, help='optimization')

    parser.add_argument('--parameters', '-params', nargs='+', type=float, default=[],
                        required=False, help='parameters for optimization')

    return parser


def get_output_directory_and_path(script_name, filename, fromdate, todate):
    modpath = os.path.dirname(os.path.abspath(script_name))
    output_directory = os.path.join(modpath, 'reports', os.path.splitext(os.path.basename(filename))[0])
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    output_filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_report_from_{fromdate.strftime("%Y%m%d_%H%M%S")}_to_{todate.strftime("%Y%m%d_%H%M%S")}'
    output_path = os.path.join(output_directory, output_filename)

    return output_directory, output_path


def get_default_cerebro(model='', scaler='', csv='', dataname='', prediction=-1, symbol='EURUSD', period='H1',
                        fromdate=date(2021, 1, 1), todate=date(2022, 1, 1),
                        optimization=False, cash=200000, leverage=1, **kwargs):

    # create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Set our desired cash start
    cash = cash
    cerebro.broker.setcash(cash)

    leverage = leverage
    margin = cash / leverage

    cerebro.broker.addcommissioninfo(ForexCommission(leverage=leverage, margin=margin))

    # add analyzers
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
    cerebro.addanalyzer(bt.analyzers.Transactions, headers=True)

    if dataname:
        data = DownloadedCSVData(dataname=dataname, openinterest=prediction)

    else:
        _, timeframe, compression, = PERIODS[period]
        data = PSQLData(symbol=symbol,
                        period=period,
                        timeframe=timeframe,
                        compression=compression,
                        fromdate=fromdate,
                        todate=todate)

    cerebro.adddata(data, name=symbol)

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    output_filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_report_from_{fromdate.strftime("%Y%m%d_%H%M%S")}_to_{todate.strftime("%Y%m%d_%H%M%S")}'
    output_directory = os.path.join(modpath, 'reports', output_filename)
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_directory, output_filename)

    if not optimization:
        cerebro.addobserver(bt.observers.Broker)
        cerebro.addobserver(bt.observers.BuySell, barplot=True, bardist=0.0020)
        cerebro.addobserver(bt.observers.Trades, pnlcomm=True)
        cerebro.addwriter(bt.WriterFile, out=output_path, rounding=5, csv=False)

    return cerebro, output_directory

from backtrader_plotly.plotter import BacktraderPlotly
from backtrader_plotly.scheme import PlotScheme
from datetime import date, datetime
from pathlib import Path
from utils.analyzers import MultiSymbolsTradeAnalyzer, MultiSymbolsTransactions
from utils.commissions import ForexCommission
from utils.constants import PERIODS, SYMBOLS
from utils.datafeeds import DownloadedCSVData, PSQLData
from utils.strategies import CurrencyStrength
import argparse
import backtrader as bt
import os
import plotly.io
import sys


def parse_args():
    parser = argparse.ArgumentParser(description='CS')

    parser.add_argument('--datadirectory', '-dd', dest='data_directory',
                        default='', required=False,
                        help='data directory for all csv files', metavar='FILE')

    parser.add_argument('--period', '-p', choices=PERIODS.keys(),
                        default='D1', required=False,
                        help='timeframe period to be traded.')

    parser.add_argument('--fromdate', '-from', type=date.fromisoformat,
                        default=date(2021, 1, 1),
                        required=False, help='date starting the trade.')

    parser.add_argument('--todate', '-to', type=date.fromisoformat,
                        default=date(2022, 1, 1),
                        required=False, help='date ending the trade.')

    return parser.parse_args()


def get_datas_from_psql(period, fromdate, todate):
    datas = {}
    _, timeframe, compression, = PERIODS[period]

    for price_type in ('BID', 'ASK'):
        for symbol in SYMBOLS:
            data_name = f'{symbol}_{price_type}'

            data = PSQLData(symbol=symbol,
                            price_type=price_type,
                            period=period,
                            timeframe=timeframe,
                            compression=compression,
                            fromdate=fromdate,
                            todate=todate)

            if price_type == 'ASK':
                data.compensate(datas[f'{symbol}_BID'])
                data.plotinfo.plotmaster = datas[f'{symbol}_BID']

            datas[data_name] = data

    return datas


# Collect data from folder
def collect_data_from_folder(data_directory, fromdate, todate):
    datas = {}

    bid_price_path = os.path.join(data_directory, 'bid')
    ask_price_path = os.path.join(data_directory, 'ask')

    bid_file_list = list(Path(bid_price_path).glob('*.csv'))
    ask_file_list = list(Path(ask_price_path).glob('*.csv'))

    # Add bid prices data first
    for file_path in bid_file_list:
        file_name = file_path.parts[-1]
        symbol = file_name[:6] + '_BID'
        data = DownloadedCSVData(dataname=file_path,
                                 fromdate=fromdate,
                                 todate=todate,)
        datas[symbol] = data

    # Add ask prices data
    for file_path in ask_file_list:
        file_name = file_path.parts[-1]
        symbol = file_name[:6] + '_ASK'
        data = DownloadedCSVData(dataname=file_path,
                                 fromdate=fromdate,
                                 todate=todate,)

        # data compensation
        data.compensate(datas[symbol[:6] + '_BID'])
        data.plotinfo.plotmaster = datas[symbol[:6] + '_BID']

        datas[symbol] = data

    return datas


def backtest(data_directory, period, fromdate, todate):
    # create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Set our desired cash start
    cash = 100000
    cerebro.broker.setcash(cash)

    # Add strategy
    cerebro.addstrategy(CurrencyStrength, period=14,)

    # Add commission scheme
    leverage = 1
    margin = cash / leverage
    for price_type in ('BID', 'ASK'):
        for symbol in SYMBOLS:
            if 'JPY' in symbol:
                cerebro.broker.addcommissioninfo(ForexCommission(commission=0.0035,
                                                                 leverage=leverage,
                                                                 margin=margin,
                                                                 ),
                                                 name=f'{symbol}_{price_type}')
            else:
                cerebro.broker.addcommissioninfo(ForexCommission(commission=0.000035,
                                                                 leverage=leverage,
                                                                 margin=margin,
                                                                 ),
                                                 name=f'{symbol}_{price_type}')

    # Add analyzer
    cerebro.addanalyzer(MultiSymbolsTradeAnalyzer)
    cerebro.addanalyzer(MultiSymbolsTransactions, headers=True)

    # Add writer
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    output_directory = os.path.join(modpath, 'reports', os.path.splitext(os.path.basename(__file__))[0])
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    output_filename = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_report_from_{fromdate.strftime("%Y%m%d_%H%M%S")}_to_{todate.strftime("%Y%m%d_%H%M%S")}'
    output_path = os.path.join(output_directory, output_filename)
    cerebro.addwriter(bt.WriterFile, out=output_path, rounding=5, csv=False)

    # Add data
    if data_directory:
        data_directory = os.path.join(modpath, data_directory)
        datas = collect_data_from_folder(data_directory, fromdate, todate)
    else:
        datas = get_datas_from_psql(period, fromdate, todate)

    for name, data in datas.items():
        cerebro.adddata(data, name=name)

    # Print out the starting conditions
    print(f'Starting Portfolio Value: {cerebro.broker.getvalue():.2f}')

    # Run over everything
    runstrats = cerebro.run(runonce=False, stdstats=False)

    figs = cerebro.plot(BacktraderPlotly(show=True, scheme=PlotScheme()))
    figs = [x for fig in figs for x in fig]  # flatten output

    for fig in figs:
        plotly.io.to_html(fig, full_html=False)  # open html in the browser
        plotly.io.write_html(fig, file=f'{output_path}.html')  # save the html file

    # Print out the final result
    print(f'Final Portfolio Value: {cerebro.broker.getvalue():.2f}')
    print(f'Net   Portfolio Value: {cerebro.broker.getvalue() - cash:.2f}')


def main():
    args = parse_args()
    backtest(args.data_directory, args.period, args.fromdate, args.todate)


if __name__ == '__main__':
    # 13_cs_backtest.py -dd ./data/forex_2021/day_bar
    main()

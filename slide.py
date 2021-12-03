from datetime import datetime, timedelta, date
from pathlib import Path
from utils.commissions import ForexCommission
from utils.constants import *
from utils.datafeeds import DownloadedCSVData
from utils.psql import PSQLData
from utils.strategies import MovingAveragesCrossover, RSIPositionSizing
from utils.testcases import slides_generator
from utils.plotter import BacktraderPlottly

import argparse
import os
import sys
import utils.optimizations as utils_opt
import plotly.io


def parse_args():
    parser = argparse.ArgumentParser(description='Random Trading')

    parser.add_argument('--symbol', '-s', choices=SYMBOLS,
                        default='EURUSD', required=False,
                        help='symbols to be traded.')

    parser.add_argument('--period', '-p', choices=PERIODS.keys(),
                        default='H1', required=False,
                        help='timeframe period to be traded.')

    parser.add_argument('--fromdate', '-from', type=date.fromisoformat,
                        default=(date.today() - timedelta(days=365 * 5)),
                        required=False, help='date starting the trade.')

    parser.add_argument('--todate', '-to', type=date.fromisoformat,
                        default=date.today(),
                        required=False, help='date ending the trade.')

    parser.add_argument('--strength', '-str', nargs='?', default=0, const=0.0005,
                        help='auto size by strength')

    parser.add_argument('--optimization', '-o', nargs='?', default=0, const=16,
                        help='optimization mode')

    return parser.parse_args()


def backtest(symbol, period, fromdate, todate, strength, optimization):
    # create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Set our desired cash start
    cash = 200000
    cerebro.broker.setcash(cash)

    leverage = 1
    margin = cash / leverage

    cerebro.broker.addcommissioninfo(ForexCommission(leverage=leverage, margin=margin))

    _, timeframe, compression, = PERIODS[period]

    data = PSQLData(symbol=symbol,
                    period=period,
                    timeframe=timeframe,
                    compression=compression,
                    fromdate=fromdate,
                    todate=todate)

    data = DownloadedCSVData(dataname='./data/EURUSD_from_20201130_to_20211129_D1_BID.csv')

    cerebro.adddata(data)

    # add analyzers
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.Returns)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)
    # cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Months, compression=1)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer)
    cerebro.addanalyzer(bt.analyzers.Transactions, headers=True)

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

        if strength:
            cerebro.addstrategy(RSIPositionSizing,
                                print_log=True,
                                period=14,
                                upper_unwind=30.0,
                                lower_unwind=70.0,
                                )
        else:
            '''
            cerebro.addstrategy(RSIPositionSizing,
                                print_log=True,
                                period=14,
                                upper_unwind=30.0,
                                lower_unwind=70.0,
                                )
            '''
            cerebro.addstrategy(MovingAveragesCrossover,
                                fast_ma_period=3,
                                slow_ma_period=20,
                                )

        cerebro.run(runonce=False, stdstats=False)
        print(f'Starting Portfolio Value: {cash:.2f}')
        print(f'Net   Portfolio Value: {cerebro.broker.getvalue() - cash:.2f}')
        figs = cerebro.plot(BacktraderPlottly())
        figs = [x for fig in figs for x in fig]  # flatten output
        for i, fig in enumerate(figs):
            plotly.io.write_html(fig, f'fig{i}')

    else:
        strats = []
        optimizer = utils_opt.Optimizer(cerebro,
                                        RSIPositionSizing,
                                        slides_generator,
                                        datetime_from=datetime.combine(fromdate, datetime.min.time()),
                                        datetime_before=datetime.combine(todate, datetime.min.time()),
                                        durations=[timedelta(days=30 * (i + 1)) for i in range(3)],
                                        steps=[timedelta(days=1)],
                                        period=14,
                                        upper_unwind=30.0,
                                        lower_unwind=70.0,
                                        )

        '''
        optimizer = utils_opt.Optimizer(cerebro,
                                        BuyAndHold,
                                        slides_generator,
                                        datetime_from=datetime.combine(fromdate, datetime.min.time()),
                                        datetime_before=datetime.combine(todate, datetime.min.time()),
                                        durations=[timedelta(days=30 * (i + 1)) for i in range(3)],
                                        steps=[timedelta(days=1)],
                                        )
        '''

        runstrat = optimizer.start()
        strats = [x[0] for x in runstrat]  # flatten the result

        if strats:
            utils_opt.save_strats(strats, output_path,)


def main(args):
    backtest(args.symbol,
             args.period,
             args.fromdate,
             args.todate,
             args.strength,
             args.optimization,
             )


if __name__ == '__main__':
    args = parse_args()
    main(args)

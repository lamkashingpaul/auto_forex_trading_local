from datetime import datetime, timedelta, date
from pathlib import Path
from utils.commissions import ForexCommission
from utils.testcases import slides_generator
from utils.constants import *
from utils.psql import PSQLData
from utils.strategies import BuyAndHold, RSIPositionSizing

import argparse
import os
import pickle
import sys
import utils.optimizations as utils_opt


def parse_args():
    parser = argparse.ArgumentParser(description='Random Trading')

    parser.add_argument('--symbol', '-s', choices=SYMBOLS,
                        default='EURUSD', required=False,
                        help='symbols to be traded.')

    parser.add_argument('--period', '-p', choices=PERIODS.keys(),
                        default='H1', required=False,
                        help='timeframe period to be traded.')

    parser.add_argument('--fromdate', '-from', type=date.fromisoformat,
                        default=(date.today() - timedelta(days=365)),
                        required=False, help='date starting the trade.')

    parser.add_argument('--todate', '-to', type=date.fromisoformat,
                        default=date.today(),
                        required=False, help='date ending the trade.')

    parser.add_argument('--strength', '-str', nargs='?', default=0, const=0.0005,
                        help='auto size by strength')

    parser.add_argument('--optimization', '-o', nargs='?', default=0, const=16,
                        help='optimization mode')

    parser.add_argument('--filename', '-f', default=None, required=False,
                        help='Filename of pickled runstrat')

    parser.add_argument('--nopickle', '-np', action='store_true',
                        help='Filename of pickled runstrat')

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
        cerebro.addobserver(bt.observers.Value)
        cerebro.addobserver(bt.observers.BuySell, barplot=True, bardist=0.0020)
        cerebro.addobserver(bt.observers.Trades, pnlcomm=True)

        if args.nopickle:
            cerebro.addwriter(bt.WriterFile, out=output_path, rounding=5, csv=False)

        if strength:
            cerebro.addstrategy(RSIPositionSizing,
                                print_log=True,
                                use_strength=True,
                                period=14,
                                )
        else:
            cerebro.addstrategy(RSIPositionSizing,
                                print_log=True,
                                period=14,
                                )

        runstrat = cerebro.run(runonce=False, stdstats=False)
        print(f'Starting Portfolio Value: {cash:.2f}')
        print(f'Net   Portfolio Value: {cerebro.broker.getvalue() - cash:.2f}')

        if not args.nopickle:
            runstrat = runstrat[0]  # flatten the result
            pickle.dump(runstrat, open(f'{output_path}.pickle', 'wb'))

        plot = cerebro.plot(style='candlestick', barup='green', bardown='red', rowsmajor=1, rowsminor=1)
        pickle.dump(plot, open(f'{output_path}_plot.pickle', 'wb'))

    else:
        strats = []
        optimizer = utils_opt.Optimizer(cerebro,
                                        RSIPositionSizing,
                                        slides_generator,
                                        datetime_from=datetime.combine(fromdate, datetime.min.time()),
                                        datetime_before=datetime.combine(todate, datetime.min.time()),
                                        duration=timedelta(days=90),
                                        step=timedelta(days=30),
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
                                        duration=timedelta(days=90),
                                        step=timedelta(days=30),
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


def plot_cash(filepath):
    strats = pickle.load(open(filepath, 'rb'))

    timeline = [bt.num2date(time_in_float) for time_in_float in strats.array]
    cash_line = [cash for cash in strats.stats.broker.array]
    trade_line = [trade for trade in strats.stats.trades.array]


if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)

    args = parse_args()

    if args.filename:

        filepath = os.path.join(script_dir, args.filename)
        plot_cash(filepath)

        strats = pickle.load(open(filepath, 'rb'))
        print(strats)
    else:
        main(args)
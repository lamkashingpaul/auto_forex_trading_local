from datetime import datetime, timedelta, date
from pathlib import Path
from utils.commission import ForexCommission
from utils.constants import *
from utils.psql import PSQLData
from utils.strategies import MovingAveragesCrossover

import argparse
import itertools
import os
import random
import sys
import utils.optimization as utils_opt


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

    return parser.parse_args()


def testcase_generator(max_period, n=0):
    max_period += 1

    if n == 0:
        testcases = itertools.product(range(1, max_period), range(1, max_period), (0.0001, 0.0005, 0.0010))
        for fast_ma_period, slow_ma_period, strength in testcases:
            if fast_ma_period != slow_ma_period:
                for use_strength in (True, False):
                    yield dict(use_strength=use_strength,
                               strength=strength,
                               fast_ma_period=fast_ma_period,
                               slow_ma_period=slow_ma_period,
                               )
    else:
        for _ in range(n):
            fast_ma_period, slow_ma_period = random.sample(range(1, max_period), 2)
            for use_strength in (True, False):
                for strength in (0.0001, 0.0005, 0.0010):
                    yield dict(use_strength=use_strength,
                               strength=strength,
                               fast_ma_period=fast_ma_period,
                               slow_ma_period=slow_ma_period,
                               )


def backtest(symbol, period, fromdate, todate, strength, optimization):
    # create a cerebro entity
    cerebro = bt.Cerebro(stdstats=False)

    # Set our desired cash start
    cash = 150000
    cerebro.broker.setcash(cash)

    cerebro.broker.addcommissioninfo(ForexCommission())

    data = PSQLData(symbol=symbol, period=period, fromdate=fromdate, todate=todate)

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
        cerebro.addobserver(bt.observers.BuySell, barplot=True, bardist=0.0001)
        cerebro.addobserver(bt.observers.Trades, pnlcomm=True)

        cerebro.addwriter(bt.WriterFile, out=output_path, rounding=5, csv=False)

        if strength:
            strength = float(strength)
            print(strength)
            cerebro.addstrategy(MovingAveragesCrossover,
                                print_log=True,
                                use_strength=True,
                                strength=strength,
                                )
        else:
            cerebro.addstrategy(MovingAveragesCrossover, print_log=True)

        cerebro.run(runonce=False, stdstats=False)
        print(f'Starting Portfolio Value: {cash:.2f}')
        print(f'Net   Portfolio Value: {cerebro.broker.getvalue() - cash:.2f}')
        cerebro.plot(style='candlestick', barup='green', bardown='red')

    else:
        strats = []
        num_of_samples = int(optimization)
        optimizer = utils_opt.Optimizer(cerebro, MovingAveragesCrossover, testcase_generator, 20, num_of_samples)

        runstrat = optimizer.start()
        strats = [x[0] for x in runstrat]  # flatten the result

        if strats:
            utils_opt.save_strats(strats, output_path,)


def main(args):
    backtest(args.symbol, args.period, args.fromdate, args.todate, args.strength, args.optimization)


if __name__ == '__main__':
    args = parse_args()
    main(args)

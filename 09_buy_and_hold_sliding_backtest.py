from utils.optimizations import OptimizerCLI
from utils.strategies import BuyAndHold
from utils.testcases import slides_generator

import backtest_basic
import inspect
import os
import plotly_basic


def optimization():
    args = backtest_basic.get_default_parser('Buy and Hold Sliding Backtest').parse_args()

    cerebro, output_directory = backtest_basic.get_default_cerebro(**vars(args))

    # process command line arguments into a list of parameters
    parameters = inspect.signature(slides_generator).bind(args.fromdate, args.todate, *args.parameters)
    parameters.apply_defaults()
    parameters = parameters.arguments

    optimizer = OptimizerCLI(cerebro, BuyAndHold, slides_generator,
                             **parameters,
                             )

    optimizer.start()

    filename = os.path.join(output_directory, 'strats')

    optimizer.save_strats(filename)


def main():
    optimization()


if __name__ == '__main__':
    # 09_buy_and_hold_sliding_backtest.py -from 2016-01-01 -to 2021-01-01 -o -params 90 1 -d ./data/forex_2016_2021/hour_bar/bid/EURUSD_from_20160101_to_20211231_H1_BID.csv
    main()

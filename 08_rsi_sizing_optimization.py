from utils.optimizations import OptimizerCLI
from utils.strategies import RSIPositionSizing
from utils.testcases import rsi_sizing_testcase_generator

import backtest_basic
import inspect
import os
import plotly_basic


def optimization():
    args = backtest_basic.get_default_parser('RSI Sizing Optimization').parse_args()

    cerebro, output_directory = backtest_basic.get_default_cerebro(**vars(args))

    # process command line arguments into a list of parameters
    parameters = inspect.signature(rsi_sizing_testcase_generator).bind(*args.parameters)
    parameters.apply_defaults()
    parameters = parameters.arguments

    optimizer = OptimizerCLI(cerebro, RSIPositionSizing, rsi_sizing_testcase_generator,
                             **parameters,
                             )

    optimizer.start()

    filename = os.path.join(output_directory, 'strats')

    optimizer.save_strats(filename)

    plotly_basic.plot_2d_heatmap('period', 'size_multiplier', 'returns_rtot', f'{filename}.csv', filename)


def main():
    optimization()  # Net Portfolio Value: 55298.098895 (period = 2, upperband = 60, lowerband = 30, upper_unwind = 40, lower_unwind = 60, size_multiplier = 0.45)

    # manual plot only
    # plotly_basic.plot_2d_heatmap('period', 'size_multiplier', 'returns_rtot',
    #                              './reports/08_rsi_sizing_optimization/strats.csv',
    #                              './reports/08_rsi_sizing_optimization/strats')


if __name__ == '__main__':
    # 08_rsi_sizing_optimization.py -o -params 0 20 0.0 0.5 0.05 30.0 40.0 60.0 70.0 5.0 -d ./data/forex_2021/hour_bar/bid/EURUSD_from_20210101_to_20211231_H1_BID.csv
    main()

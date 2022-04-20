from utils.optimizations import OptimizerCLI
from utils.strategies import MovingAveragesCrossover
from utils.testcases import sma_strength_testcase_generator

import backtest_basic
import inspect
import os
import plotly_basic


def optimization():
    args = backtest_basic.get_default_parser('SMA Signal Strength Optimization').parse_args()

    cerebro, output_directory = backtest_basic.get_default_cerebro(**vars(args))

    # process command line arguments into a list of parameters
    parameters = inspect.signature(sma_strength_testcase_generator).bind(*args.parameters)
    parameters.apply_defaults()
    parameters = parameters.arguments

    optimizer = OptimizerCLI(cerebro, MovingAveragesCrossover, sma_strength_testcase_generator,
                             **parameters,
                             )

    optimizer.start()

    filename = os.path.join(output_directory, 'strats')

    optimizer.save_strats(filename)

    plotly_basic.plot_3d_heatmap_with_cluster('slow_ma_period', 'fast_ma_period', 'strength', 'returns_rtot', f'{filename}.csv', filename)


def main():
    optimization()  # Net Portfolio Value: 12136 (strength = 0.0001, fast_ma_period = 4, slow_ma_period = 3)

    # manual plot only
    # plotly_basic.plot_3d_heatmap_with_cluster('slow_ma_period', 'fast_ma_period', 'strength', 'returns_rtot',
    #                                           './reports/04_sma_signal_strength_optimization/strats.csv',
    #                                           './reports/04_sma_signal_strength_optimization/strats')


if __name__ == '__main__':
    # 04_sma_signal_strength_optimization.py -o -params 0 20 0.001 0.0001 -d ./data/forex_2021/hour_bar/bid/EURUSD_from_20210101_to_20211231_H1_BID.csv
    main()

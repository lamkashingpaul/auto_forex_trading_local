from utils.optimizations import OptimizerCLI
from utils.strategies import RSIPositionSizing
from utils.testcases import rsi_testcase_generator
import backtest_basic
import inspect
import os
import plotly_basic


def optimization():
    args = backtest_basic.get_default_parser('Sample RSI Optimization').parse_args()

    cerebro, output_directory = backtest_basic.get_default_cerebro(**vars(args))

    # process command line arguments into a list of parameters
    parameters = inspect.signature(rsi_testcase_generator).bind(*args.parameters)
    parameters.apply_defaults()
    parameters = parameters.arguments

    optimizer = OptimizerCLI(cerebro, RSIPositionSizing, rsi_testcase_generator,
                             **parameters,
                             )

    optimizer.start()

    filename = os.path.join(output_directory, 'strats')

    optimizer.save_strats(filename)

    plotly_basic.plot_3d_heatmap_with_cluster('period', 'upperband', 'lowerband', 'returns_rtot', f'{filename}.csv', filename)


def main():
    optimization()  # Net Portfolio Value: 15932.5 (period = 18, upperband = 63, lowerband = 31)

    # manual plot only
    # plotly_basic.plot_2d_heatmap('slow_ma_period', 'fast_ma_period', 'returns_rtot',
    #                              './reports/06_sample_rsi_optimization/strats.csv',
    #                              './reports/06_sample_rsi_optimization/strats')


if __name__ == '__main__':
    # 06_sample_rsi_optimization.py -o -params 0 20 30 40 60 70 1 -d ./data/forex_2021/hour_bar/bid/EURUSD_from_20210101_to_20211231_H1_BID.csv
    main()

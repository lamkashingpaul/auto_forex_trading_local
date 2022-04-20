from utils.optimizations import OptimizerCLI
from utils.strategies import MovingAveragesCrossover
from utils.testcases import sma_testcase_generator
import backtest_basic
import inspect
import os
import plotly_basic


def optimization():
    args = backtest_basic.get_default_parser('Sample SMA Optimization').parse_args()

    cerebro, output_directory = backtest_basic.get_default_cerebro(**vars(args))

    # process command line arguments into a list of parameters
    parameters = inspect.signature(sma_testcase_generator).bind(*args.parameters)
    parameters.apply_defaults()
    parameters = parameters.arguments

    optimizer = OptimizerCLI(cerebro, MovingAveragesCrossover, sma_testcase_generator,
                             **parameters,
                             )

    optimizer.start()

    filename = os.path.join(output_directory, 'strats')

    optimizer.save_strats(filename)

    plotly_basic.plot_2d_heatmap('slow_ma_period', 'fast_ma_period', 'returns_rtot', f'{filename}.csv', filename)


def main():
    optimization()  # Net Portfolio Value: 12798.5 (fast_ma_period = 33, slow_ma_period = 17)

    # manual plot only
    # plotly_basic.plot_2d_heatmap('slow_ma_period', 'fast_ma_period', 'returns_rtot',
    #                              './reports/02_sample_sma_optimization/strats.csv',
    #                              './reports/02_sample_sma_optimization/strats')


if __name__ == '__main__':
    # 02_sample_sma_optimization.py -o -params 0 50 -d ./data/forex_2021/hour_bar/bid/EURUSD_from_20210101_to_20211231_H1_BID.csv
    main()

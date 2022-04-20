from utils.strategies import MovingAveragesCrossover
import backtest_basic
import plotly_basic


def main():
    args = backtest_basic.get_default_parser('Sample SMA Backtest').parse_args()

    cerebro, output_directory = backtest_basic.get_default_cerebro(**vars(args))

    cerebro.addstrategy(MovingAveragesCrossover)

    start_cash = cerebro.broker.getvalue()

    print(f'Starting Portfolio Value: {start_cash:.2f}')
    # Starting Portfolio Value: 200000.00

    cerebro.run(runonce=False, stdstats=False)

    print(f'Net   Portfolio Value: {cerebro.broker.getvalue() - start_cash:.2f}')
    # Net   Portfolio Value: -107.50

    # plot the results
    plotly_basic.plot_backtest_result(cerebro, output_directory)


if __name__ == '__main__':
    # 01_sample_sma_backtest.py -d ./data/forex_2021/hour_bar/bid/EURUSD_from_20210101_to_20211231_H1_BID.csv
    main()

from utils.strategies import ForecastTrading
import backtest_basic
import plotly_basic


def main():
    args = backtest_basic.get_default_parser('LSTM Prediction Backtest').parse_args()

    cerebro, output_directory = backtest_basic.get_default_cerebro(**vars(args))

    cerebro.addstrategy(ForecastTrading, print_log=True)

    start_cash = cerebro.broker.getvalue()

    print(f'Starting Portfolio Value: {start_cash:.2f}')
    # Starting Portfolio Value: 200000.00

    cerebro.run(runonce=False, stdstats=False)

    print(f'Net   Portfolio Value: {cerebro.broker.getvalue() - start_cash:.2f}')

    # plot the results
    plotly_basic.plot_backtest_result(cerebro, output_directory)


if __name__ == '__main__':
    # 18_lstm_prediction_backtest.py -pred 6 -d ./reports/add_prediction/20220423_191807_report_from_20210101_000000_to_20220101_000000_60_1_prediction.csv
    # pnl: 8826.50

    # 18_lstm_prediction_backtest.py -pred 6 -d ./reports/add_prediction/20220423_191814_report_from_20210101_000000_to_20220101_000000_600_10_prediction.csv
    # pnl: 4865.00

    main()

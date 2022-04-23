from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import backtest_basic
import math
import pandas as pd
import plotly_basic
import sys


def main():
    args = backtest_basic.get_default_parser('Linear Regression Price Prediction Model').parse_args()
    dataname = args.dataname

    fromdate = datetime.combine(args.fromdate, datetime.min.time())
    todate = datetime.combine(args.todate, datetime.min.time())

    # read csv file
    df = pd.read_csv(dataname)
    df['Datetime'] = pd.to_datetime(df['Datetime'], dayfirst=True)

    # use last prices for linear regression
    df['last_close'] = df['Close'].shift(1)
    df['last_open'] = df['Open'].shift(1)
    df['last_high'] = df['High'].shift(1)
    df['last_low'] = df['Low'].shift(1)
    df = df.dropna()

    x = df[['last_close', 'last_open', 'last_high', 'last_low']]
    y = df['Close']
    time = df['Datetime']

    t = 0.8  # use 80% of data for training and 20% for testing
    t = math.ceil(t * len(y))

    x_train, y_train = x[:t], y[:t]

    x_test, y_test = x[t:], y[t:]
    time_test = time[t:]

    linear = LinearRegression().fit(x_train, y_train)  # train the model
    y_predicted = pd.DataFrame(linear.predict(x_test).reshape(-1, 1), columns=['Predicted'])

    # concatenate columns
    df = pd.concat([time_test.reset_index(drop=True),
                    y_test.reset_index(drop=True),
                    y_predicted.reset_index(drop=True)],
                   axis=1)

    # get last year's prices
    df = df.loc[(fromdate <= df['Datetime']) & (df['Datetime'] < todate)]

    x = df['Datetime']
    y = df['Close']
    y_predicted = df['Predicted']

    print(f'r2_score = {r2_score(y, y_predicted)}')  #
    print(f'mean_absolute_error = {mean_absolute_error(y, y_predicted)}')  #
    print(f'mean_squared_error = {mean_squared_error(y, y_predicted)}')  #

    '''
    hour bar
    r2_score = 0.9991094327766409
    mean_absolute_error = 0.0005785457550307648
    mean_squared_error = 0.0005790240384615379
    '''

    _, output_path = backtest_basic.get_output_directory_and_path(sys.argv[0], __file__, args.fromdate, args.todate)
    plotly_basic.plot_real_and_prediction_with_residual(x, y, y_predicted, output_path, show=False)


if __name__ == '__main__':
    # 15_linear_regression_price_prediction_model.py -from 2011-01-01 -to 2021-01-01 -d ./data/forex_2011_2020/hour_bar/bid/EURUSD_from_20110101_to_20201231_H1_BID.csv

    main()

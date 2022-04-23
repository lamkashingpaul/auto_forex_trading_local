from datetime import datetime
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import backtest_basic
import pandas as pd
import plotly_basic
import sys


def main():
    args = backtest_basic.get_default_parser('Basic Price Prediction Model').parse_args()
    dataname = args.dataname

    fromdate = datetime.combine(args.fromdate, datetime.min.time())
    todate = datetime.combine(args.todate, datetime.min.time())

    # read csv file
    df = pd.read_csv(dataname)
    df['Datetime'] = pd.to_datetime(df['Datetime'], dayfirst=True)

    # basic prediction using last close price
    df['Predicted'] = df['Close'].shift(1).fillna(df['Close'])

    # get last year's prices
    df = df.loc[(fromdate <= df['Datetime']) & (df['Datetime'] < todate)]

    x = df['Datetime']
    y = df['Close']
    y_predicted = df['Predicted']

    print(f'r2_score = {r2_score(y, y_predicted)}')
    print(f'mean_absolute_error = {mean_absolute_error(y, y_predicted)}')
    print(f'mean_squared_error = {mean_squared_error(y, y_predicted)}')

    '''
    hour bar
    r2_score = 0.9998555958131278
    mean_absolute_error = 0.0008374906985695042
    mean_squared_error = 1.7644509189171855e-06
    '''

    _, output_path = backtest_basic.get_output_directory_and_path(sys.argv[0], __file__, args.fromdate, args.todate)
    plotly_basic.plot_real_and_prediction_with_residual(x, y, y_predicted, output_path, show=False)


if __name__ == '__main__':
    # 14_basic_price_prediction_model.py -from 2011-01-01 -to 2021-01-01 -d ./data/forex_2011_2020/hour_bar/bid/EURUSD_from_20110101_to_20201231_H1_BID.csv

    main()

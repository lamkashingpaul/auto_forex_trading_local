from datetime import datetime
from keras.callbacks import CSVLogger
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras import layers
import backtest_basic
import joblib
import math
import numpy as np
import pandas as pd
import plotly_basic
import sys
import tensorflow as tf

pd.options.mode.chained_assignment = None
tf.random.set_seed(0)


def main():
    args = backtest_basic.get_default_parser('Long Short Term Memory Price Prediction Model').parse_args()
    _, output_path = backtest_basic.get_output_directory_and_path(sys.argv[0], __file__, args.fromdate, args.todate)
    dataname = args.dataname

    # fromdate = datetime.combine(args.fromdate, datetime.min.time())
    # todate = datetime.combine(args.todate, datetime.min.time())

    # read csv file
    df = pd.read_csv(dataname)
    df['Datetime'] = pd.to_datetime(df['Datetime'], dayfirst=True)

    y = df['Close'].fillna(method='ffill')
    y = y.values.reshape(-1, 1)

    if args.model and args.scaler:
        # load trained model from directory
        # no training is done here, 100% for testing
        t = 0

        scaler = joblib.load(args.scaler)
        model = keras.models.load_model(args.model)
        _, n_lookback, _ = model.input_shape
        _, n_forecast = model.output_shape

        y = scaler.transform(y)

        # create test data
        test_data = y[t:]
        x_test, y_test = [], []
        for i in range(n_lookback, len(test_data) - n_forecast + 1):
            x_test.append(test_data[i - n_lookback: i])
            y_test.append(test_data[i: i + n_forecast])

        x_test, y_test = np.array(x_test), np.array(y_test)
        time_test = df['Datetime'][t:]

    else:
        # use 80% of data for training and 20% for testing
        t = 0.8
        t = math.ceil(t * len(y))

        # price data normalization
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaler = scaler.fit(y)

        y = scaler.transform(y)

        # define lookback and forecast windows size
        n_lookback = 60
        n_forecast = 5

        # create train data windows of size n_lookback
        train_data = y[:t]
        x_train, y_train = [], []
        for i in range(n_lookback, len(train_data) - n_forecast + 1):
            x_train.append(train_data[i - n_lookback: i])
            y_train.append(train_data[i: i + n_forecast])

        x_train, y_train = np.array(x_train), np.array(y_train)

        # create test data
        test_data = y[t:]
        x_test, y_test = [], []
        for i in range(n_lookback, len(test_data) - n_forecast + 1):
            x_test.append(test_data[i - n_lookback: i])
            y_test.append(test_data[i: i + n_forecast])

        x_test, y_test = np.array(x_test), np.array(y_test)
        time_test = df['Datetime'][t:]

        # define model training logger
        csv_logger = CSVLogger(f'{output_path}_training.log')

        # create LSTM model
        model = keras.Sequential()
        model.add(layers.LSTM(units=100, return_sequences=True, input_shape=(n_lookback, 1)))
        model.add(layers.LSTM(units=100, return_sequences=True))
        model.add(layers.LSTM(units=100))
        model.add(layers.Dense(n_forecast))
        model.summary()

        # train and save LSTM model
        optimizer = keras.optimizers.Adam(learning_rate=0.005)
        model.compile(optimizer=optimizer, loss='mean_squared_error', metrics=['mean_absolute_error', 'mean_squared_error'])
        model.fit(x_train, y_train, batch_size=32, epochs=128, validation_split=0.2, callbacks=[csv_logger])

        model.save(f'{output_path}_trained_lstm_model.h5', save_format='h5')  # save model
        joblib.dump(scaler, f'{output_path}_scaler.bin', compress=True)

    # predict future prices
    x_test = [x.reshape(1, n_lookback, 1) for x in x_test]
    y_predicted = [scaler.inverse_transform(model.predict(x).reshape(-1, 1)) for x in x_test]
    y_test = [scaler.inverse_transform(y.reshape(-1, 1)) for y in y_test]

    y_test, y_predicted = np.array(y_test).squeeze(), np.array(y_predicted).astype(np.float64).squeeze()

    # calculate metrics
    print(f'r2_score = {r2_score(y_test, y_predicted)}')
    print(f'mean_absolute_error = {mean_absolute_error(y_test, y_predicted)}')
    print(f'mean_squared_error = {mean_squared_error(y_test, y_predicted)}')

    '''
    hour bar (n_lookback = 60, n_forecast = 1, lr=0.005)
    r2_score = 0.9990731340754265
    mean_absolute_error = 0.0007303255908631959
    mean_squared_error = 1.1177164773934462e-06

    hour bar (n_lookback = 600, n_forecast = 10, lr=0.005)
    r2_score = 0.9953133676760908
    mean_absolute_error = 0.0017802945017196376
    mean_squared_error = 5.862390470963261e-06

    day bar close price (n_lookback = 60, n_forecast = 1, lr=0.005)
    r2_score = 0.9850548105754098
    mean_absolute_error = 0.0032479854584415387
    mean_squared_error = 1.9807706438586098e-05

    day bar open price (n_lookback = 60, n_forecast = 1, lr=0.005)
    r2_score = 0.963246566244455
    mean_absolute_error = 0.005924528643987875
    mean_squared_error = 4.816842186826988e-05

    day bar close price (n_lookback = 60, n_forecast = 5, lr=0.005)
    r2_score = 0.9492502349545558
    mean_absolute_error = 0.005825799943716558
    mean_squared_error = 6.671470455828521e-05

    '''

    # generate n_forecast predictions plot
    # y_test = pd.Series(scaler.inverse_transform(y[t:]).squeeze())  # get original close price
    if n_forecast > 1:
        y_predicted = y_predicted[:, -1].squeeze()

    y_n_th_prediction = pd.Series(y_predicted)  # n_th prediction from today

    df = pd.concat([time_test.reset_index(drop=True),
                    df['Close'][t:].reset_index(drop=True),
                    y_n_th_prediction.reset_index(drop=True),
                    ],
                   keys=['Datetime', 'Close', 'N_Predict'], axis=1)

    df['N_Predict'] = df['N_Predict'].shift(n_lookback).fillna(df['Close'])

    x = df['Datetime']
    y = df['Close']
    y_predicted = df['N_Predict']

    plotly_basic.plot_real_and_prediction_with_residual(x, y, y_predicted, output_path, show=True)


if __name__ == '__main__':
    # 16_lstm_price_prediction_model.py -from 2011-01-01 -to 2021-01-01 -d ./data/forex_2011_2020/hour_bar/bid/EURUSD_from_20110101_to_20201231_H1_BID.csv

    # 16_lstm_price_prediction_model.py -from 2011-01-01 -to 2021-01-01 -d ./data/forex_2011_2020/day_bar/bid/EURUSD_from_20110101_to_20201231_D1_BID.csv

    main()

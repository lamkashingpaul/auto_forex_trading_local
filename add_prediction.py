from tensorflow import keras
import backtest_basic
import joblib
import numpy as np
import pandas as pd
import sys


def main():
    args = backtest_basic.get_default_parser('Add Prediction to CSV').parse_args()
    _, output_path = backtest_basic.get_output_directory_and_path(sys.argv[0], __file__, args.fromdate, args.todate)

    df = pd.read_csv(args.dataname)

    y = df['Close'].fillna(method='ffill')
    y = y.values.reshape(-1, 1)

    model = keras.models.load_model(args.model)
    _, n_lookback, _ = model.input_shape
    _, n_forecast = model.output_shape

    scaler = joblib.load(args.scaler)
    y = scaler.transform(y)

    X = [y[i - n_lookback:i].reshape(1, n_lookback, 1) for i in range(n_lookback, len(y) - n_forecast + 1)]
    Y = [scaler.inverse_transform(model.predict(x).reshape(-1, 1)) for x in X]

    y_predicted = np.array(Y).astype(np.float64).squeeze()
    if n_forecast > 1:
        y_predicted = y_predicted[:, -1].squeeze()

    y_n_th_prediction = pd.Series(y_predicted)  # n_th prediction from today
    df['Prediction'] = y_n_th_prediction

    if args.align:
        df['Prediction'] = df['Prediction'].shift(n_lookback - 1).fillna(df['Close'])

    df.to_csv(f'{output_path}_{n_lookback}_{n_forecast}_prediction.csv', index=False)


if __name__ == '__main__':
    # add_prediction.py -m ./models/hour_bar_predict_1_bar_training_lr_0.005_trained_lstm_model.h5 -sc ./models/hour_bar_predict_1_bar_training_lr_0.005_scaler.bin -a-d ./data/forex_2021/hour_bar/bid/EURUSD_from_20210101_to_20211231_H1_BID.csv

    # add_prediction.py -m ./models/hour_bar_predict_10_bar_training_lr_0.005_trained_lstm_model.h5 -sc ./models/hour_bar_predict_10_bar_training_lr_0.005_scaler.bin -a -d ./data/forex_2021/hour_bar/bid/EURUSD_from_20210101_to_20211231_H1_BID.csv

    main()

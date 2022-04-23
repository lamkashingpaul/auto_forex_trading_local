from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.models import Sequential
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

pd.options.mode.chained_assignment = None
tf.random.set_seed(0)


# unseen data
df = pd.read_csv('./data/2020.csv')

y = df['Close'].fillna(method='ffill')
y = y.values.reshape(-1, 1)

model = keras.models.load_model('./models/example.h5')
_, n_lookback, _ = model.input_shape
_, n_forecast = model.output_shape

scaler = joblib.load('./models/example_scaler.bin')
y = scaler.transform(y)


'''
# download the data
df = pd.read_csv('./data/2020.csv')

y = df['Close'].fillna(method='ffill')
y = y.values.reshape(-1, 1)

# scale the data
scaler = MinMaxScaler(feature_range=(0, 1))
scaler = scaler.fit(y)

y = scaler.transform(y)

# generate the input and output sequences
n_lookback = 60  # length of input sequences (lookback period)
n_forecast = 30  # length of output sequences (forecast period)

X = []
Y = []

for i in range(n_lookback, len(y) - n_forecast + 1):
    X.append(y[i - n_lookback: i])
    Y.append(y[i: i + n_forecast])

X = np.array(X)
Y = np.array(Y)

# fit the model
model = Sequential()
model.add(LSTM(units=50, return_sequences=True, input_shape=(n_lookback, 1)))
model.add(LSTM(units=50))
model.add(Dense(n_forecast))

model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(X, Y, epochs=100, batch_size=32)

model.save('./models/example.h5', save_format='h5')
joblib.dump(scaler, './models/example_scaler.bin', compress=True)
'''


# (1, 60, 1) * 224
X_ = [y[i - n_lookback:i].reshape(1, n_lookback, 1) for i in range(n_lookback, len(y) - n_forecast + 1)]
Y_ = [scaler.inverse_transform(model.predict(x).reshape(-1, 1)) for x in X_]
last_col = np.array(Y_)[:, -1].squeeze()

# organize the results in a data frame
df_past = df[['Close']].reset_index()
df_past.rename(columns={'index': 'Date', 'Close': 'Actual'}, inplace=True)
df_past['Date'] = pd.to_datetime(df['Datetime'], dayfirst=True)

df_past['Today_Forecast'] = pd.Series(last_col)
df_past['Today_Forecast'] = df_past['Today_Forecast'].shift(n_lookback)

# plot the results
import matplotlib.pyplot as plt
df_past.set_index('Date').plot(title='Test')
plt.show()

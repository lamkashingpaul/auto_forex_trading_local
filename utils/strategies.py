import backtrader as bt


class BuyAndHold(bt.Strategy):

    params = (
        ('one_lot_size', 100000),
    )

    def log(self, txt, dt=None, doprint=True):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def start(self):
        # keep the starting cash
        self.val_start = self.broker.get_cash()

    def nextstart(self):
        # buy all with the available cash
        lots = int(self.broker.get_cash() / self.data / self.p.one_lot_size)
        self.buy(size=lots * self.p.one_lot_size)

    def stop(self):
        # calculate the actual returns
        self.roi = (self.broker.get_value() / self.val_start) - 1.0
        print(f'B&H ROI: {100.0 * self.roi:.2f}%')


class MovingAveragesCrossover(bt.Strategy):

    params = (
        ('print_log', False),
        ('optimization_dict', dict()),

        ('use_strength', False),
        ('strength', 0.0005),

        ('one_lot_size', 100000),

        ('fast_ma_period', 50),
        ('slow_ma_period', 200),

    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.print_log or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f' BUY EXECUTED, '
                         f'Price: {order.executed.price:>9.5f}, '
                         f'Cost: {order.executed.value:>9.2f}, '
                         f'Comm: {order.executed.comm:>9.2f}',
                         dt=bt.num2date(order.executed.dt))
            else:  # Sell
                self.log(f'SELL EXECUTED, '
                         f'Price: {order.executed.price:>9.5f}, '
                         f'Cost: {order.executed.value:>9.2f}, '
                         f'Comm: {order.executed.comm:>9.2f}',
                         dt=bt.num2date(order.executed.dt))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'({bt.num2date(trade.dtopen)}), {trade.data._name}, '
                 f'Gross: {trade.pnl:>9.2f}, '
                 f'Net : {trade.pnlcomm:>9.2f}, ',
                 dt=bt.num2date(trade.dtclose))

    def __init__(self):
        if self.p.optimization_dict:
            for key, value in self.p.optimization_dict.items():
                setattr(self.p, key, value)

        self.fast_sma = fast_sma = bt.ind.SMA(period=self.p.fast_ma_period)  # fast moving average
        self.slow_sma = slow_sma = bt.ind.SMA(period=self.p.slow_ma_period)  # slow moving average
        self.crossover = bt.ind.CrossOver(fast_sma, slow_sma)  # crossover signal
        self.strength = bt.ind.SMA(abs(fast_sma - fast_sma(-1)), period=1, subplot=True)

    def next(self):

        size = self.p.one_lot_size

        if not self.position:  # not in the market
            if self.crossover != 0:  # if there is signal
                if self.crossover < 0:  # negate the size
                    size = -size

                # only open position if signal is strong
                if self.p.use_strength and self.strength.lines.sma[0] < self.p.strength:
                    return

                # open position with target size
                self.log(f'fast: {self.fast_sma.lines.sma[0]:.5f}, slow: {self.slow_sma.lines.sma[0]:.5f}, diff: {self.strength.lines.sma[0]:.5f}')
                self.order_target_size(target=size)

        else:  # in the market
            if self.position.size > 0 and self.crossover < 0:  # having buy position and sell signal
                size = -size
            elif self.position.size < 0 and self.crossover > 0:  # having sell position and buy signal
                pass
            else:
                return

            # if this is retrived, one wants to reverse his position
            # if signal is not strong enough, close instead of reverse current position
            if self.p.use_strength and self.strength.lines.sma[0] < self.p.strength:
                size = 0

            self.log(f'fast: {self.fast_sma.lines.sma[0]:.5f}, slow: {self.slow_sma.lines.sma[0]:.5f}, diff: {self.strength.lines.sma[0]:.5f}')
            self.order_target_size(target=size)


class RSIPositionSizing(bt.Strategy):

    params = (
        ('print_log', False),
        ('optimization_dict', dict()),

        ('use_strength', False),

        ('one_lot_size', 100000),

        ('period', 2),
        ('upperband', 75.0),
        ('lowerband', 25.0),

        ('upper_unwind', 65.0),
        ('lower_unwind', 35.0),

        ('size_multiplier', 0.15),

    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.print_log or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f' BUY EXECUTED, '
                         f'Price: {order.executed.price:>9.5f}, '
                         f'Cost: {order.executed.value:>9.2f}, '
                         f'Comm: {order.executed.comm:>9.2f}',
                         dt=bt.num2date(order.executed.dt))
            else:  # Sell
                self.log(f'SELL EXECUTED, '
                         f'Price: {order.executed.price:>9.5f}, '
                         f'Cost: {order.executed.value:>9.2f}, '
                         f'Comm: {order.executed.comm:>9.2f}',
                         dt=bt.num2date(order.executed.dt))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'({bt.num2date(trade.dtopen)}), {trade.data._name}, '
                 f'Gross: {trade.pnl:>9.2f}, '
                 f'Net : {trade.pnlcomm:>9.2f}, ',
                 dt=bt.num2date(trade.dtclose))

    def __init__(self):
        if self.p.optimization_dict:
            for key, value in self.p.optimization_dict.items():
                setattr(self.p, key, value)

        self.max_buy_position = float('-inf')
        self.max_sell_position = float('inf')

        self.rsi = bt.ind.RSI(period=self.p.period, upperband=self.p.upperband, lowerband=self.p.lowerband, safediv=True)

        self.buy_signal = self.rsi < self.p.lowerband
        self.sell_signal = self.rsi > self.p.upperband

    def next(self):
        size = self.p.one_lot_size

        if self.p.use_strength:
            if not self.position.size:
                if self.buy_signal:
                    size_multiplier = (self.p.lowerband - self.rsi) * self.p.size_multiplier
                    size = max(size, size * size_multiplier)
                    self.order_target_size(target=size)

                elif self.sell_signal:
                    size_multiplier = (self.rsi - self.p.upperband) * self.p.size_multiplier
                    size = max(size, size * size_multiplier)
                    self.order_target_size(target=-size)

            else:
                if self.position.size > 0 and self.rsi > self.p.lower_unwind:
                    self.close()
                elif self.position.size < 0 and self.p.upper_unwind > self.rsi:
                    self.close()
        else:
            if not self.position.size:
                if self.buy_signal:
                    self.buy(size=size)
                elif self.sell_signal:
                    self.sell(size=size)
            else:
                if ((self.position.size > 0 and self.sell_signal) or
                        (self.position.size < 0 and self.buy_signal)):
                    self.order_target_size(target=-self.position.size)

                pass

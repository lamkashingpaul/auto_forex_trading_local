import backtrader as bt


class MovingAveragesCrossover(bt.Strategy):

    params = (
        ('print_log', False),
        ('optimization_dict', dict()),

        ('use_strength', False),
        ('strength', 0.001),

        ('one_lot_size', 100000),

        ('fast_ma_period', 14),
        ('slow_ma_period', 40),

    )

    def log(self, txt, dt=None, doprint=True):
        ''' Logging function fot this strategy'''
        if self.params.print_log or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

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

        fast_sma = bt.ind.SMA(period=self.p.fast_ma_period)  # fast moving average
        slow_sma = bt.ind.SMA(period=self.p.slow_ma_period)  # slow moving average
        self.crossover = bt.ind.CrossOver(fast_sma, slow_sma)  # crossover signal
        self.difference = bt.ind.SMA(abs(fast_sma - slow_sma), subplot=True)

    def next(self):

        size = self.p.one_lot_size
        if self.p.use_strength:
            size *= self.get_size_multiplier_by_strength()

        if not self.position:  # not in the market
            if self.crossover != 0:  # if there is signal

                if self.crossover < 0:  # negate the size
                    size = -size

                # open position with target size
                print(self.difference.lines.sma[0])
                self.order_target_size(target=size)

        else:  # in the market
            if self.position.size > 0 and self.crossover < 0:  # having buy position and sell signal
                size = -size
            elif self.position.size < 0 and self.crossover > 0:  # having sell position and buy signal
                pass
            else:
                return

            # if this is retrived, one wants to reverse his position
            print(self.difference.lines.sma[0])
            self.order_target_size(target=size)

    def get_size_multiplier_by_strength(self):
        return round(self.difference.lines.sma[0] / self.p.strength, 1)
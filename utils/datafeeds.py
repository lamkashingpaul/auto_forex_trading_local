import backtrader as bt


class DownloadedCSVData(bt.feeds.GenericCSVData):
    # default parameters
    params = (
        ('nullvalue', 0.0),
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
        ('tmformat', '%H:%M:%S'),
        ('timeframe', bt.TimeFrame.Minutes),
        ('compression', 60),

        ('datetime', 0),
        ('time', -1),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', -1),
    )

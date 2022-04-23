from pathlib import Path
import backtest_basic
import os
import plotly_basic
import sys


def main():
    args = backtest_basic.get_default_parser('Sliding Comparison').parse_args()

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    output_directory = os.path.join(modpath, 'reports', os.path.splitext(os.path.basename(__file__))[0])
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    output = os.path.join(output_directory, 'strats')

    plotly_basic.plot_sliding_comparison(args.dataname, args.csv, output)


if __name__ == '__main__':
    # 12_sliding_comparison.py -d ./data/forex_2016_2021/hour_bar/bid/EURUSD_from_20160101_to_20211231_H1_BID.csv -c ./reports/09_buy_and_hold_sliding_backtest/strats.csv ./reports/10_sma_strength_sliding_backtest/strats.csv ./reports/11_rsi_sizing_sliding_backtest/strats.csv
    main()

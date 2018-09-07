import numpy as np
import pandas as pd
import queue
from multiprocessing import Pool
import os
import talib 


from setting import set_env
global back_config
back_config = set_env()
from Backtest import *
from Backtest.open_json_gz_files import open_json_gz_files
from Backtest.generate_bars import generate_bars


class CMOStrategy(Strategy):
    def __init__(self, config, events, data_handler,
                 window = 10):
        self.config = config
        self.data_handler = data_handler
        self.tickers = self.config['tickers']
        self.events = events
        self.holdinds = self._calculate_initial_holdings()

        self.window = window 

    def _calculate_initial_holdings(self):
        holdings = {}
        for s in self.tickers:
            holdings[s] = "EMPTY"
        return holdings


    def generate_signals(self, event):
        if event.type == EventType.MARKET:
            ticker = event.ticker
            bar_date = event.timestamp
            bars_close = self.data_handler.get_latest_bars_values(ticker, "close", N = self.window + 1)

            if len(bars_close) == self.window + 1:
                CMO = talib.CMO(bars_close, timeperiod=self.window)[-1]
                if CMO > 0 and self.holdinds[ticker] == "EMPTY":
                    self.generate_buy_signals(ticker, bar_date, "LONG")
                    self.holdinds[ticker] = "HOLD"
                elif CMO < 0 and self.holdinds[ticker] == "HOLD":
                    self.generate_sell_signals(ticker, bar_date, "SHORT")
                    self.holdinds[ticker] = "EMPTY"


def run_backtest(config, trading_data, ohlc_data, window = 10):
    config['title'] = "CMOStrategy" + "_" + str(window)
    print("---------------------------------")
    print(config['title'])
    print("---------------------------------")
    
    events_queue = queue.Queue()

    data_handler = OHLCDataHandler(
        config, events_queue,
        trading_data = trading_data, ohlc_data = ohlc_data
    )
    strategy = CMOStrategy(config, events_queue, data_handler,
                           window = window)

    backtest = Backtest(config, events_queue, strategy,
                        data_handler= data_handler)

    results = backtest.start_trading()
    return backtest, results
    
    # dict_ans = {
    #     "window": [window],
    #     "Sharpe Ratio": [results['sharpe']],
    #     "Total Returns": [(results['cum_returns'][-1] - 1)],
    #     "Max Drawdown": [(results["max_drawdown"] * 100.0)],
    #     "Max Drawdown Duration": [(results['max_drawdown_duration'])],
    #     "Trades": [results['trade_info']['trading_num']],
    #     "Trade Winning": [results['trade_info']['win_pct']],
    #     "Average Trade": [results['trade_info']['avg_trd_pct']],
    #     "Average Win": [results['trade_info']['avg_win_pct']],
    #     "Average Loss": [results['trade_info']['avg_loss_pct']],
    #     "Best Trade": [results['trade_info']['max_win_pct']],
    #     "Worst Trade": [results['trade_info']['max_loss_pct']],
    #     "Worst Trade Date": [results['trade_info']['max_loss_dt']],
    #     "Avg Days in Trade": [results['trade_info']['avg_dit']]
    # }
    # return pd.DataFrame(dict_ans)

if __name__ == "__main__":
    config = {
        "csv_dir": back_config['data_folder'],
        "out_dir": os.path.join(back_config['output_folder'], "CMOStrategy"),
        "title": "CMOStrategy",
        "is_plot": False,
        "save_plot": True,
        "save_tradelog": True,
        # "start_date": pd.Timestamp("2018-02-01T00:0:00", freq = "60" + "T"),    # str(freq) + "T"
        # "end_date": pd.Timestamp("2018-06-01T00:00:00", freq = "60" + "T"),
        "start_date": pd.Timestamp("2018-06-01T00:0:00", freq = "60" + "T"),    # str(freq) + "T"
        "end_date": pd.Timestamp("2018-09-01T00:00:00", freq = "60" + "T"),
        "equity": 1.0,
        "freq": 60,      # min
        "commission_ratio": 0.001,
        "suggested_quantity": None,     # None or a value
        "max_quantity": None,           # None or a value, Maximum purchase quantity
        "min_quantity": None,           # None or a value, Minimum purchase quantity
        "min_handheld_cash": None,      # None or a value, Minimum handheld funds
        "exchange": "Binance",
        "tickers": ['BTCUSDT']
    }

    # trading_data = {}
    # for ticker in config['tickers']:
    #     # trading_data[ticker] = open_gz_files(config['csv_dir'], ticker)
    #     trading_data[ticker] = pd.read_hdf(config['csv_dir'] + '\\' + ticker + '.h5', key=ticker)

    ohlc_data = {}
    for ticker in config['tickers']:
        # ohlc_data[ticker] = generate_bars(trading_data, ticker, config['freq'])
        ohlc_data[ticker] = pd.read_hdf(config['csv_dir'] + '/' + ticker +'_OHLC_60min.h5', key=ticker)

    trading_data = None

    backtest, results = run_backtest(config, trading_data, ohlc_data, window = 146)



    # interval = np.array([5, 10, 12, 26, 30, 35, 45, 60, 72, 84, 96, 120, 252])
    # # interval = np.array([5, 12, 26, 45, 60, 96, 120, 252])
    # # interval = np.array([5, 30, 120])
    #
    # pool = Pool(4)
    # results = []
    # for i in range(len(interval)):
    #     window = interval[i]
    #     result = pool.apply_async(run_backtest, args=(config, trading_data, ohlc_data, window,))
    #     results.append(result)
    #
    # ans = pd.DataFrame()
    # for results in results:
    #     df = results.get()
    #     ans = pd.concat([ans, df], ignore_index=True)
    # pool.close()
    #
    # if not os.path.exists(config['out_dir']):
    #     os.makedirs(config['out_dir'])
    # ans = ans.sort_values(by="Total Returns", ascending=False)
    # ans.to_csv(config['out_dir'] + "/result_ADXStrategy.csv")
from config import Alpaca_key,Alpaca_secret_key,Alpaca_endpoint
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from datetime import datetime

import Trading
from Portfolio import is_ticker_owned_already
import Data

today=datetime.today()
market_open = today.replace(hour=7, minute=30, second=0, microsecond=0)
pre_market_open = today.replace(hour=7, minute=0, second=0, microsecond=0)
ten_minutes_before_close = today.replace(hour=13, minute=50, second=0, microsecond=0)

def append_bar_SMAs(data):
    """
        Arguements:
        data -> Historical price data. 
            Required:
                type: Pandas Dataframe 
                shape: (date, open, high, low, close, volume)
        
        Returns:
        Returns inputted Pandas Dataframe of historical price data with 5, 8, 13 bar SMA's appended as new columns
    """
    bar_5 = []
    bar_8 = []
    bar_13 = []
    for index, bar in data.iterrows():
        # Creating SMA's
        close = bar["close"]
        # 5 bar MA
        if len(bar_5) < 5:
            bar_5.append(close)
            bar_5_MA = np.mean(bar_5)
        else:
            bar_5.pop(0)
            bar_5.append(close)
            bar_5_MA = np.mean(bar_5)
        # 8 bar MA
        if len(bar_8) < 8:
            bar_8.append(close)
            bar_8_MA = np.mean(bar_8)
        else:
            bar_8.pop(0)
            bar_8.append(close)
            bar_8_MA = np.mean(bar_8)
        # 13 bar MA
        if len(bar_13) < 13:
            bar_13.append(close)
            bar_13_MA = np.mean(bar_13)
        else:
            bar_13.pop(0)
            bar_13.append(close)
            bar_13_MA = np.mean(bar_13)
        # Adding values to dataframe for analysis
        data.at[index, "5_bar_SMA"] = bar_5_MA
        data.at[index, "8_bar_SMA"] = bar_8_MA
        data.at[index, "13_bar_SMA"] = bar_13_MA
    return data

def append_bar_EMAs(data, alpha=0.0):
    data["5_bar_EMA"] = data['close'].transform(lambda x: x.ewm(span=5).mean())
    data["8_bar_EMA"] = data['close'].transform(lambda x: x.ewm(span=8).mean())
    data["13_bar_EMA"] = data['close'].transform(lambda x: x.ewm(span=13).mean())
    return data

def append_signals_and_indicators(data, fast_MA_column: str, slow_MA_column: str):
    """
        Arguements:
        data -> Historical price dataframe including MA's of choice
        
        Returns:
        Returns inputted Pandas Dataframe of historical price data with buy signals appended as new columns
    """
    # Setting inital momentum variable
    if data.iloc[0][fast_MA_column] - data.iloc[0][slow_MA_column] > 0:
        old_momentum = "bullish"
    else:
        old_momentum = "bearish"

    for index, row in data.iterrows():
        fast = row[fast_MA_column]
        slow = row[slow_MA_column]

        if fast > slow:
            momentum = "bullish"
        else:
            momentum = "bearish"

        if (momentum == old_momentum) and (momentum == "bullish"):
            signal = "long"
        elif (momentum == old_momentum) and (momentum == "bearish"):
            signal = "short"
        elif momentum != old_momentum:
            if (old_momentum == "bullish") and (momentum == "bearish"):
                signal = "sell"
            elif (old_momentum == "bearish") and (momentum == "bullish"):
                signal = "buy"

        difference = fast - slow

        data.at[index, "momentum"] = momentum
        data.at[index, "difference"] = difference
        data.at[index, "signal"] = signal

        old_momentum = momentum
    return data

def count_signals(list_of_words):
    counts = {}
    for signal in list_of_words:
        if signal in counts.keys():
            counts[signal] += 1
        else:
            counts[signal] = 1
    return counts

def check_for_sell_signal(data, current_signal, ticker):
    owned, qty = is_ticker_owned_already(ticker)
    if owned:
        if current_signal == "long":
            difference = list(data["difference"][-4:])
            last_four = data.iloc[-4:]
            for index, row in last_four.iterrows():
                # If the 5 bar moving average has crossed the 8 bar moving average...
                if row["5_bar_EMA"] < row["8_bar_EMA"]:
                    # If there are three consecutive narrowing differences
                    if (difference[-1] < difference[-2]) and (difference[-2] < difference[-3]) and (difference[-3] < difference[-4]):
                        # If premarket...
                        if (datetime.now() > pre_market_open) and (datetime.now() < market_open):
                            order_number = Trading.sell_stock_limit_order(data, .03, ticker , qty)
                            Data.print_trade_update(data, ticker, False, True, 0, qty, "sell", "5_bar_EMA", "13_bar_EMA", order_number)
                            print(f"Submitted limit sell order for {ticker} before the 5_bar_EMA crossed the 13_bar_EMA because the 5_bar_EMA crossed the 8_bar_EMA and there were 3 consecutive narrowing differences.")
                        else:
                            order_number = Trading.sell_stock(ticker, qty)
                            Data.print_trade_update(data, ticker, False, True, 0, qty, "sell", "5_bar_EMA", "13_bar_EMA", order_number)
                            print(f"Submitted sell order for {ticker} before the 5_bar_EMA crossed the 13_bar_EMA because the 5_bar_EMA crossed the 8_bar_EMA and there were 3 consecutive narrowing differences.")
        elif current_signal == "short":
            difference = list(data["difference"][-4:])
            last_four = data.iloc[-4:]
            for index, row in last_four.iterrows():
                # If the 5 bar moving average has crossed the 8 bar moving average...
                if row["5_bar_EMA"] > row["8_bar_EMA"]:
                    # If there are three consecutive narrowing differences
                    if (abs(difference[-1]) < abs(difference[-2])) and (abs(difference[-2]) < abs(difference[-3])) and (abs(difference[-3]) < abs(difference[-4])):
                        # If premarket...
                        if (datetime.now() > pre_market_open) and (datetime.now() < market_open):
                            order_number = Trading.buy_stock_limit_order(data, .03, ticker , qty)
                            Data.print_trade_update(data, ticker, True, True, 0, qty, "buy", "5_bar_EMA", "13_bar_EMA", order_number)
                            print(f"Submitted limit buy order for {ticker} to cover short position before the 5_bar_EMA crossed the 13_bar_EMA because the 5_bar_EMA crossed the 8_bar_EMA and there were 3 consecutive narrowing differences.")
                        else:
                            order_number = Trading.buy_stock(ticker, qty)
                            Data.print_trade_update(data, ticker, True, True, 0, qty, "buy", "5_bar_EMA", "13_bar_EMA", order_number)
                            print(f"Submitted buy order for {ticker} to cover short position before the 5_bar_EMA crossed the 13_bar_EMA because the 5_bar_EMA crossed the 8_bar_EMA and there were 3 consecutive narrowing differences.")

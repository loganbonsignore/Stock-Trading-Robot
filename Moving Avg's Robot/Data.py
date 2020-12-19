from config import Alpaca_key,Alpaca_secret_key,Alpaca_endpoint
import alpaca_trade_api as tradeapi
import pandas as pd
from datetime import datetime
import sys
import time

# import pytz
# time_zone = pytz.timezone('US/Mountain')

import Indicators

fast_MA = "5_bar_EMA"
slow_MA = "13_bar_EMA"

# API Auth
api = tradeapi.REST(Alpaca_key,Alpaca_secret_key,Alpaca_endpoint)

def get_price_dataframe(ticker="SPY",length="5Min",limit=100): # limit= 1Min, 5Min, 15Min, or 1D
    """
        Arguements:
            ticker -> Stock ticker symobl (default SPY)
            length -> Amount of time between bars (default 5Min)
            limit -> Number of bars returned (default 100)
            
        Returns:
        Returns a Pandas Dataframe of historical price data for any given ticker
    """
    # Submitting request
    barset=api.get_barset(ticker,length,limit)
    # Creating Dataframe
    data = pd.DataFrame()
    for bar in barset[ticker]:
        close=bar.c
        open=bar.o
        high=bar.h
        low=bar.l
        volume=bar.v
        datetime=bar.t
        if len(data) == 0:
            index = [0]
        else:
            index = [max(data.index)+1]
        new_row = pd.DataFrame({
            "date":datetime,
            "open":open,
            "high":high,
            "low":low,
            "close":close,
            "volume":volume}, index=index)
        data = data.append(new_row)
    return data

def get_current_bar(data, ticker, length="5Min", limit=1):
    """
        Arguements:
        data -> Historical price dataframe EXCLUDING MA's of choice
        ticker -> ticker you want bar to retrieve
        length -> Amount of time in between bars
        limit -> Number of bars to retrieve (default=1)
        
        Returns:
        Returns inputted Pandas Dataframe of historical price data with 1 appended new row of current market data
        Returns "Record previously obtained" when new data is already detected as last row in dataframe
    """
    bar=api.get_barset(ticker,length,limit)
    close=bar[ticker][0].c
    open=bar[ticker][0].o
    high=bar[ticker][0].h
    low=bar[ticker][0].l
    volume=bar[ticker][0].v
    datetime=bar[ticker][0].t
    
    # Check to see if already have data
    if bar[ticker][0].t == data.iloc[-1]["date"]:
        # Already in DF, don't add
        # Run again in one minute
        return "Record previously obtained"
    # Setting index to add new row to
    if len(data) == 0:
        index = [0]
    else:
        index = [max(data.index)+1]
    # Adding new row
    new_row = pd.DataFrame({
        "date":datetime,
        "open":open,
        "high":high,
        "low":low,
        "close":close,
        "volume":volume}, index=index)
    data = data.append(new_row)
    return data

def get_updated_data(ticker, fast_MA, slow_MA):
    if ("EMA" in fast_MA) and ("EMA" in slow_MA):
        data = get_price_dataframe(ticker)
        Indicators.append_bar_EMAs(data)
        data = Indicators.append_signals_and_indicators(data, fast_MA, slow_MA)
    elif ("SMA" in fast_MA) and ("SMA" in slow_MA):
        data = get_price_dataframe(ticker)
        Indicators.append_bar_SMAs(data)
        data = Indicators.append_signals_and_indicators(data, fast_MA, slow_MA)
    else:
        sys.exit("Fast_MA and Slow_MA must be a supported moving average. They must also be the same category of moving average.")
    return data

def print_signal_update(data, signal, fast_MA, slow_MA):
    current_data = data.iloc[-1]
    print(f"********Signal: {signal}, Price: {round(current_data['close'], 10)}, Fast Moving Avg: {round(current_data[fast_MA], 10)}, 8 Bar EMA: {round(current_data['8_bar_EMA'], 10)} Slow Moving Avg: {round(current_data[slow_MA], 10)}, Time: {datetime.now()}********")

def print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number):
    slow_MA = data.iloc[-1][slow_MA]
    fast_MA = data.iloc[-1][fast_MA]
    order = api.get_order_by_client_order_id(order_number)
    # If trade is confirmed to be filled...
    if order.status == "filled":
        trade_time = order.filled_at
        price = order.filled_avg_price
        trade_qty = order.filled_qty

        if (current_signal == "buy") and (short):
            print(f"""Short Cover Order Filled:
    Ticker: {ticker}
    Price: {price}
    Qty: {trade_qty}
    Fast Moving Avg: {fast_MA}
    Slow Moving Avg: {slow_MA}
    Filled at: {trade_time}
    Order Number: {order_number}
""")
        elif (current_signal == "buy") and (not owned) and (not short):
            print(f"""Buy Order Filled:
    Ticker: {ticker}
    Price: {price}
    Qty: {trade_qty}
    Fast Moving Avg: {fast_MA}
    Slow Moving Avg: {slow_MA}
    Filled at: {trade_time}
    Order Number: {order_number}
""")
        elif (current_signal == "sell") and (not short) and (owned):
            print(f"""Sell Order Filled:
    Ticker: {ticker}
    Price: {price}
    Qty: {trade_qty}
    Fast Moving Avg: {fast_MA}
    Slow Moving Avg: {slow_MA}
    Filled at: {trade_time}
    Order Number: {order_number}
""")
        elif (current_signal == "sell") and (not owned):
            print(f"""Short Order Filled:
    Ticker: {ticker}
    Price: {price}
    Qty: {trade_qty}
    Fast Moving Avg: {fast_MA}
    Slow Moving Avg: {slow_MA}
    Filled at: {trade_time}
    Order Number: {order_number}
""")
        elif (current_signal == "long") and (not owned):
            print(f"""Buy Order Filled:
    Ticker: {ticker}
    Price: {price}
    Qty: {trade_qty}
    Fast Moving Avg: {fast_MA}
    Slow Moving Avg: {slow_MA}
    Filled at: {trade_time}
    Order Number: {order_number}
""")
        elif (current_signal == "short") and (not owned):
            print(f"""Sell Order Filled:
    Ticker: {ticker}
    Price: {price}
    Qty: {trade_qty}
    Fast Moving Avg: {fast_MA}
    Slow Moving Avg: {slow_MA}
    Filled at: {trade_time}
    Order Number: {order_number}
""")
        elif (current_signal == "long") and (owned):
            print(f"No trade executed, {ticker} is already owned in your portfolio.")
    else:
        return order.status
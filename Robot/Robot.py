from config import Alpaca_key,Alpaca_secret_key,Alpaca_endpoint
import alpaca_trade_api as tradeapi
from datetime import datetime
import time
import sys

# import pytz
# time_zone = pytz.timezone('US/Mountain')

import Data
import Indicators
import Trading
import Portfolio

api = tradeapi.REST(Alpaca_key,Alpaca_secret_key,Alpaca_endpoint)
account = api.get_account()

today=datetime.today()
market_open = today.replace(hour=7, minute=30, second=0, microsecond=0)
pre_market_open = today.replace(hour=7, minute=0, second=0, microsecond=0)
ten_minutes_before_close = today.replace(hour=13, minute=50, second=0, microsecond=0)

################################################################################################################################
################################################################################################################################

# Check if account blocked from trading
if account.trading_blocked:
    sys.exit("Account Blocked From Trading by Alpaca")

# Ticker to trade
ticker = input("""
Which ticker do you want to trade? :""")
asset = api.get_asset(ticker)
if (not asset.tradable) or (not asset.shortable):
    if (asset.tradable) and (not asset.shortable):
        sys.exit(f"Alpaca does not support shorting of {ticker}")
    else:
        sys.exit(f"Alpaca does not support trading of {ticker}")


# Qty of security to buy and sell at each execution
print(f"Current Buying Power Available: {account.buying_power}")
user_input = input("Choose buy quantity based on buying power or hard-coded share count? ('bp' or 'qty') :")
if user_input == 'bp':
    designated_buying_power = float(input(f"""How much buying power do you want to allocate towards {ticker}? :"""))
    cash_available_for_trade = float(account.buying_power)
    current_price = float(api.get_barset(ticker, "5Min", 1)[ticker][0].c)
    if cash_available_for_trade >= designated_buying_power:    
        buy_qty = designated_buying_power // current_price
        print(f"Chosen Trade Quantity: {buy_qty}")
    else:
        buy_qty = cash_available_for_trade // current_price
        print(f"Not enough buying power, using maximum trade quantity based on available buying power: {buy_qty}")
elif user_input == "qty":
    buy_qty = float(input("How many units would you like to trade? :"))
else:
    sys.exit("Cannot understand input. Try again.")

# Moving averages used to indicate buy or sell
print('''
Moving Average Options:
Exponential Moving Averages:
    "5_bar_EMA",
    "8_bar_EMA",
    "13_bar_EMA"
Simple Moving Averages:
    "5_bar_SMA",
    "8_bar_SMA",
    "13_bar_SMA"
''')

fast_MA = input("Enter selected Fast Moving Average :")
slow_MA = input("Enter selected Slow Moving Average :")

################################################################################################################################
################################################################################################################################

# If in pre-market...
if (datetime.now() > pre_market_open) and (datetime.now() < market_open):
    while (datetime.now() > pre_market_open) and (datetime.now() < market_open):
        # Get updated data
        data = Data.get_updated_data(ticker, fast_MA, slow_MA)
        # Get current signal
        current_signal = data.iloc[-1]["signal"]
        # Check for sell signals if already own stock
        if (current_signal == "long") or (current_signal == "short"):
            Indicators.check_for_sell_signal(data, current_signal, ticker)  # Only compatible with Exponential Moving Averages
        # Printing signal update
        Data.print_signal_update(data, current_signal, fast_MA, slow_MA)
        # Executing pre-market trade
        Trading.execute_trade_pre_market(data, current_signal, ticker, buy_qty, fast_MA, slow_MA)

        time.sleep(300)

# While market open...
while Portfolio.is_market_open():
    # Update data with most current market data
    data = Data.get_updated_data(ticker, fast_MA, slow_MA)
    # Getting current signal
    current_signal = data.iloc[-1]["signal"]
    # Check for sell signals if already own stock
    if (current_signal == "long") or (current_signal == "short"):
        Indicators.check_for_sell_signal(data, current_signal, ticker)  # Only compatible with Exponential Moving Averages
    # Printing update
    Data.print_signal_update(data, current_signal, fast_MA, slow_MA)
    # Executing trade
    Trading.execute_trade(data, current_signal, ticker, buy_qty, fast_MA, slow_MA)
    # Closing all positions 10 minutes before market close
    if (datetime.now() >= ten_minutes_before_close):
        Trading.exit_positions()

    time.sleep(300)

sys.exit("Market Closed")
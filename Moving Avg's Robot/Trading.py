from config import Alpaca_key,Alpaca_secret_key,Alpaca_endpoint
import alpaca_trade_api as tradeapi
import time
from datetime import datetime
import random
import sys

import Data
import Portfolio
import Indicators

today=datetime.today()
market_open = today.replace(hour=7, minute=30, second=0, microsecond=0)
pre_market_open = today.replace(hour=7, minute=0, second=0, microsecond=0)

# import pytz
# time_zone = pytz.timezone('US/Mountain')

api = tradeapi.REST(Alpaca_key,Alpaca_secret_key,Alpaca_endpoint)

def buy_stock(symbol='SPY',qty=1,type='market',time_in_force='gtc'):
    order_number = str(random.randint(100000000000,999999999999))
    api.submit_order(
        symbol=symbol,
        qty=qty,
        side='buy',
        type=type,
        time_in_force=time_in_force,
        client_order_id=order_number)
    return order_number

def sell_stock(symbol='SPY',qty=1,type='market',time_in_force='gtc'):
    order_number = str(random.randint(100000000000,999999999999))
    api.submit_order(
        symbol=symbol,
        qty=qty,
        side='sell',
        type=type,
        time_in_force=time_in_force,
        client_order_id=order_number)
    return order_number

# def buy_stock_limit_order(data, flex=.01, symbol='SPY',qty=1):
#     """
#         Arguements:
#         data -> Normalized historical market data
#         Flex -> The % change you are willing to pay higher than the current price ---- Adjusts limit order price by x %.
#     """
#     price = api.get_last_trade(symbol).price
#     limit_price = price + (price * flex)

#     order_number = str(random.randint(100000000000,999999999999))
#     api.submit_order(
#         symbol=symbol,
#         qty=qty,
#         side='buy',
#         type="limit",
#         time_in_force="day",
#         extended_hours=True,
#         limit_price=limit_price,
#         client_order_id=order_number)
#     return order_number

# def sell_stock_limit_order(data, flex=.01, symbol='SPY',qty=1):
#     """
#         Arguements:
#         data -> Normalized historical market data
#         Flex -> The % change you are willing to take lower than the current price ---- Adjusts limit order selling price by x %.
#     """
#     price = api.get_last_trade(symbol).price
#     limit_price = price - (price * flex)

#     order_number = str(random.randint(100000000000,999999999999))
#     api.submit_order(
#         symbol=symbol,
#         qty=qty,
#         side='sell',
#         type="limit",
#         time_in_force="day",
#         extended_hours=True,
#         limit_price=limit_price,
#         client_order_id=order_number)
#     return order_number

def short_stock(data, total_trades, trade_limit, symbol='SPY',qty=1, slow_MA="13_bar_EMA", fast_MA="5_bar_EMA"):
    # Get latest price
    price = api.get_last_trade(symbol).price
    limit_price = price - (price * .03)
    # Submit an order for one share at limit price
    order_number = str(random.randint(100000000000,999999999999))
    api.submit_order(symbol, qty, 'sell', "limit", "day", limit_price, client_order_id=order_number)
    time.sleep(1)
    slow_MA = data.iloc[-1][slow_MA]
    fast_MA = data.iloc[-1][fast_MA]
    order = api.get_order_by_client_order_id(order_number)
    # If order not filled, allow order to fill for 3 minutes
    if order.status != "filled":
        for i in range(3):
            time.sleep(60)
            order = api.get_order_by_client_order_id(order_number)
            if order.status == "filled":
                total_trades += 1
                if total_trades >= trade_limit:
                    sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
                return order_number
        # If order still not filled, cancel order
        if api.get_order_by_client_order_id(order_number).status != "filled":
            api.cancel_order(order.id)
            sys.exit(f"Short Trade for {symbol} has been cancelled. Order #{order_number} failed to fill 4 minutes after submission.")
    elif order.status == "filled":
        return order_number
    else:
        return order_number

# def exit_positions_limit(data):
#     positions=api.list_positions()
#     if positions:
#         for i in positions:
#             if int(i.qty) > 0:
#                 order_number = sell_stock_limit_order(data, flex=.05, symbol=i.symbol,qty=int(i.qty))
#             elif int(i.qty) < 0:
#                 qty = abs(int(i.qty))
#                 order_number = buy_stock_limit_order(data, flex=.05, symbol=i.symbol,qty=qty)
#     time.sleep(10)
#     positions = api.list_positions()
#     if not positions:
#         print("All positions liquidated.")
#     else:
#         print("Positions Remaining Open:")
#         count = 1
#         for i in positions:
#             print(f"Position {count}: {i.symbol}")
#             print(i)
#             count += 1

def exit_positions():
    positions=api.list_positions()
    if positions:
        for i in positions:
            if int(i.qty) > 0:
                order_number = sell_stock(symbol=i.symbol,qty=int(i.qty))
            elif int(i.qty) < 0:
                qty = abs(int(i.qty))
                order_number = buy_stock(symbol=i.symbol,qty=qty)
    time.sleep(10)
    positions = api.list_positions()
    if not positions:
        print("All positions liquidated.")
    else:
        print("Positions Remaining Open:")
        count = 1
        for i in positions:
            print(f"Position {count}: {i.symbol}")
            print(i)
            count += 1

def evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA: str, slow_MA: str, num_of_signals: int=3, num_of_checks: int=10):
    print(f"Evaluating Reverse Trade for {ticker}, {datetime.now()}")
    if current_signal == "buy":
        loop_count = 1
        for i in range(num_of_checks+1)[1:]:
            time.sleep(305)
            # Get current data
            data = Data.get_updated_data(ticker, fast_MA, slow_MA)
            # Get signal counts
            counts = Indicators.count_signals(list(data["signal"][-num_of_signals:])) 
            # Execute trade or not
            if "long" in counts:
                pass
            else:
                continue
            if counts["long"] == num_of_signals:
                # if in premarket... limit order
                if (datetime.now() > pre_market_open) and (datetime.now() < market_open):
                    # Execute trade   # Taken out because i dont want to make a reverse trade in premarket. Bad idea to invest if already making turns. Also limit order is not closed if not filled.
                    # order_number = buy_stock_limit_order(data, .03, ticker , buy_qty)
                    sys.exit(f"Reverse order would have been executed for {ticker} but has not been executed since we are in premarket trading. If a reverse has occured this early in the trading session, it may be a bad time to enter the market.")
                else:
                    # Execute trade
                    order_number = buy_stock(ticker, buy_qty)
                    return order_number
            print(f"{str(loop_count)} out of {str(num_of_checks)} Reverse Trade attempts completed for {ticker}.")
            loop_count+=1
        sys.exit(f"Reverse order for {ticker} has not been executed. This may be a bad time to enter the market.")
    elif current_signal == "sell":
        loop_count = 1
        for i in range(num_of_checks+1)[1:]:
            time.sleep(300)
            # Get current data
            data = Data.get_updated_data(ticker, fast_MA, slow_MA)
            # Get signal counts
            counts = Indicators.count_signals(list(data["signal"][-num_of_signals:])) 
            # Execute trade or not
            if "short" in counts:
                pass
            else:
                continue
            if counts["short"] == num_of_signals:
                # if in premarket... limit order
                if (datetime.now() > pre_market_open) and (datetime.now() < market_open):
                    # Execute trade   # Taken out because i dont want to make a reverse trade in premarket. Bad idea to invest if already moving reverse. Also limit order is not closed if not filled.
                    # order_number = sell_stock_limit_order(data, .03, ticker , buy_qty)
                    sys.exit(f"Reverse order would have been executed for {ticker} but has not been executed since we are in premarket trading. If a reverse has occured this early in the trading session, it may be a bad time to enter the market.")
                else:
                    # Execute trade
                    order_number = sell_stock(ticker, buy_qty)
                    return order_number
            print(f"{str(loop_count)} out of {str(num_of_checks)} Reverse Trade attempts completed for {ticker}.")
            loop_count+=1
        sys.exit(f"Reverse order for {ticker} has not been executed. This may be a bad time to enter the market.")
    else:
        print("Not enough information to trade. (No buy or sell signal passed)")



def attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA):
    # Try to buy for 5 minutes
    order = api.get_order_by_client_order_id(order_number)
    if order.status != "filled":
        print(f"Order number {order_number} for {ticker} was not immediately filled. Attempting to fill order for 5 minutes before cancelling. {datetime.now()}")
        for i in range(5):
            time.sleep(60)
            order = api.get_order_by_client_order_id(order_number)
            if order.status == "filled":
                trade_qty = order.filled_qty
                if (current_signal == "long") or (current_signal == "buy"):
                    order_status = Data.print_trade_update(data, ticker, False, False, trade_qty, trade_qty, "buy", slow_MA, fast_MA, order_number)
                elif (current_signal == "short") or (current_signal == "sell"):
                    order_status = Data.print_trade_update(data, ticker, False, True, trade_qty, trade_qty, "sell", slow_MA, fast_MA, order_number)
                return True # Order filled
        # If order still not filled, cancel order
        if api.get_order_by_client_order_id(order_number).status != "filled":
            api.cancel_order(order.id)
            print(f"Order {order_number} for {ticker} has been cancelled. Failed to fill within 5 minutes after execution.")
            return False
    elif order.status == "filled":
        return True



def execute_trade(data, current_signal, trade_limit, total_trades, ticker="SPY", buy_qty=1, fast_MA="5_bar_EMA", slow_MA="13_bar_EMA"):
    """
        Arguements:
            current_signal -> "buy", "sell", "long", "short"
            ticker -> Ticker to buy
            buy_qty -> Number of stocks to buy
            
        Returns:
        Returns None, only executes a trade
    """
    # Check for short positions
    positions=api.list_positions()
    if positions:
        for i in positions:
            if (i.symbol == ticker) and (int(i.qty) < 0):
                short = True
                break
            else:
                short = False
    else:
        short = False
                
    # Collecting information used in trading
    owned, qty = Portfolio.is_ticker_owned_already(ticker)   # qty is always a positive number, even if short

    if (current_signal == "buy") and (short):
        # Cover short order
        order_number = buy_stock(ticker, qty)
        order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
        if order_status != "filled":
            filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
            if filled_status == True:
                total_trades += 1
                if total_trades >= trade_limit:
                    sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
        else:
            filled_status = True
            total_trades += 1
            if total_trades >= trade_limit:
                sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
        # REVERSED - USE CAUTION - Buy stock
        if trade_limit >= 2:
            order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
            if order_number:
                order_status = Data.print_trade_update(data, ticker, False, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
                if order_status != "filled":
                    filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
                    if filled_status == True:
                        total_trades += 1
                else:
                    filled_status = True
                    total_trades += 1
    elif (current_signal == "buy") and (not owned):
        # Buy stock
        order_number = buy_stock(ticker, buy_qty)
        order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
        if order_status != "filled":
            filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
            if filled_status == True:
                total_trades += 1
        else:
            filled_status = True
            total_trades += 1
    elif (current_signal == "sell") and (not short):
        if owned:
            # Sell current holdings
            order_number = sell_stock(ticker, qty=qty)
            order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
            if order_status != "filled":
                filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
                if filled_status == True:
                    total_trades += 1
                    if total_trades >= trade_limit:
                        sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
            else:
                filled_status = True
                total_trades += 1
                if total_trades >= trade_limit:
                    sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
            if trade_limit >= 2:
                # REVERSED - USE CAUTION - Short the market
                order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
                if order_number:
                    order_status = Data.print_trade_update(data, ticker, True, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
                    if order_status != "filled":
                        filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
                        if filled_status == True:
                            total_trades += 1
                    else:
                        filled_status = True
                        total_trades += 1
        elif not owned:
            # Short the market
            order_number = short_stock(data, total_trades, trade_limit, ticker, buy_qty, slow_MA, fast_MA)
            order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
            if order_status != "filled":
                filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
                if filled_status == True:
                    total_trades += 1
            else:
                filled_status = True
                total_trades += 1
    elif (current_signal == "long") and (not owned):
        # Buy stock
        order_number = buy_stock(ticker, buy_qty)
        order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
        if order_status != "filled":
            filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
            if filled_status == True:
                total_trades += 1
        else:
            filled_status = True
            total_trades += 1
    elif (current_signal == "short") and (not owned):
        # Short the market
        order_number = short_stock(data, total_trades, trade_limit, ticker, buy_qty, slow_MA, fast_MA)
        order_status = Data.print_trade_update(data, ticker, True, False, buy_qty, qty, "sell", slow_MA, fast_MA, order_number)
        if order_status != "filled":
            filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
            if filled_status == True:
                total_trades += 1
        else:
            filled_status = True
            total_trades += 1
    elif (current_signal == "short") and (owned) and (not short):
        # Sell current holdings
        order_number = sell_stock(ticker, qty=qty)
        order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
        if order_status != "filled":
            filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
            if filled_status == True:
                total_trades += 1
                if total_trades >= trade_limit:
                    sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
        else:
            filled_status = True
            total_trades += 1
            if total_trades >= trade_limit:
                sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
        if trade_limit >= 2:
            # REVERSAL BE CAREFUL - Short the market
            current_signal = "sell"
            order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
            if order_number:
                order_status = Data.print_trade_update(data, ticker, True, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
                if order_status != "filled":
                    filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
                    if filled_status == True:
                        total_trades += 1
                else:
                    filled_status = True
                    total_trades += 1
    elif (current_signal == "long") and (owned) and (short):
        # Close short position
        order_number = buy_stock(ticker, qty=qty)
        current_signal = "buy"
        order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
        if order_status != "filled":
            filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
            if filled_status == True:
                total_trades += 1
                if total_trades >= trade_limit:
                    sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
        else:
            filled_status = True
            total_trades += 1
            if total_trades >= trade_limit:
                sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
        if trade_limit >= 2:
            # REVERSAL BE CAREFUL - Buy stock
            order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
            if order_number:
                order_status = Data.print_trade_update(data, ticker, False, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
                if order_status != "filled":
                    filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
                    if filled_status == True:
                        total_trades += 1
                else:
                    filled_status = True
                    total_trades += 1
    else:
        print("No trade executed.")
        filled_status = False

    # Check to see if user has reached maximum trades
    if total_trades >= trade_limit:
        sys.exit(f"Maximum trade limit reached for {today}. Total trades executed: {total_trades}")
    
    return total_trades

# def execute_trade_pre_market(data, current_signal, trade_limit, ticker="SPY", buy_qty=1, fast_MA="5_bar_EMA", slow_MA="13_bar_EMA"):
#     """
#         Arguements:
#             current_signal -> "buy", "sell", "long", "short"
#             ticker -> Ticker to buy
#             buy_qty -> Number of stocks to buy
            
#         Returns:
#         Returns None, only executes a trade
#     """
#     # Check for short positions
#     positions=api.list_positions()
#     if positions:
#         for i in positions:
#             if (i.symbol == ticker) and (int(i.qty) < 0):
#                 short = True
#                 break
#             else:
#                 short = False

#     # Collecting information used in trading
#     owned, qty = Portfolio.is_ticker_owned_already(ticker)   # qty is always a positive number, even if short
#     num_of_trades = 0

#     if (current_signal == "buy") and (short):
#         # Cover short order
#         order_number = buy_stock_limit_order(data, flex=.03, symbol=ticker,qty=qty)
#         order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#         if order_status != "filled":
#             filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#             if filled_status == True:
#                 num_of_trades += 1
#         else:
#             filled_status = True
#             num_of_trades += 1
#         # REVERSED - USE CAUTION - Buy stock
#         if trade_limit == 4:
#             order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
#             if order_number:
#                 order_status = Data.print_trade_update(data, ticker, False, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#                 if order_status != "filled":
#                     filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#                     if filled_status == True:
#                         num_of_trades += 1
#                 else:
#                     filled_status = True
#                     num_of_trades += 1
#     elif (current_signal == "buy") and (not owned):
#         # Buy stock
#         order_number = buy_stock_limit_order(data, flex=.03, symbol=ticker,qty=buy_qty)
#         order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#         if order_status != "filled":
#             filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#             if filled_status == True:
#                 num_of_trades += 1
#         else:
#             filled_status = True
#             num_of_trades += 1
#     elif (current_signal == "sell") and (not short):
#         if owned:
#             # Sell current holdings
#             order_number = sell_stock_limit_order(data, flex=.03, symbol=ticker,qty=qty)
#             order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#             if order_status != "filled":
#                 filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#                 if filled_status == True:
#                     num_of_trades += 1
#             else:
#                 filled_status = True
#                 num_of_trades += 1
#             # REVERSED - USE CAUTION - Short the market
#             if trade_limit == 4:
#                 order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
#                 if order_number:
#                     order_status = Data.print_trade_update(data, ticker, True, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#                     if order_status != "filled":
#                         filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#                         if filled_status == True:
#                             num_of_trades += 1
#                     else:
#                         filled_status = True
#                         num_of_trades += 1
#         elif not owned:
#             # Short the market
#             order_number = short_stock(data, ticker, buy_qty, slow_MA, fast_MA)
#             order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#             if order_status != "filled":
#                 filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#                 if filled_status == True:
#                     num_of_trades += 1
#             else:
#                 filled_status = True
#                 num_of_trades += 1
#     elif (current_signal == "long") and (not owned):
#         # Buy stock
#         order_number = buy_stock_limit_order(data, flex=.03, symbol=ticker,qty=buy_qty)
#         order_status = Data.print_trade_update(data, ticker, short, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#         if order_status != "filled":
#             filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#             if filled_status == True:
#                 num_of_trades += 1
#         else:
#             filled_status = True
#             num_of_trades += 1
#     elif (current_signal == "short") and (not owned):
#         # Short the market
#         order_number = short_stock(data, ticker, buy_qty, slow_MA, fast_MA)
#         order_status = Data.print_trade_update(data, ticker, True, False, buy_qty, qty, "sell", slow_MA, fast_MA, order_number)
#         if order_status != "filled":
#             filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#             if filled_status == True:
#                 num_of_trades += 1
#         else:
#             filled_status = True
#             num_of_trades += 1
#     elif (current_signal == "short") and (owned) and (not short):
#         # Sell current holdings
#         order_number = sell_stock_limit_order(data, flex=.03, symbol=ticker,qty=qty)
#         order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#         if order_status != "filled":
#             filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#             if filled_status == True:
#                 num_of_trades += 1
#         else:
#             filled_status = True
#             num_of_trades += 1
#         # REVERSAL BE CAREFUL - Short the market
#         if trade_limit == 4:
#             current_signal = "sell"
#             order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
#             if order_number:
#                 order_status = Data.print_trade_update(data, ticker, True, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#                 if order_status != "filled":
#                     filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#                     if filled_status == True:
#                         num_of_trades += 1
#                 else:
#                     filled_status = True
#                     num_of_trades += 1
#     elif (current_signal == "long") and (owned) and (short):
#         # Close short position
#         order_number = buy_stock_limit_order(data, flex=.03, symbol=ticker,qty=qty)
#         current_signal = "buy"
#         order_status = Data.print_trade_update(data, ticker, short, owned, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#         if order_status != "filled":
#             filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#             if filled_status == True:
#                 num_of_trades += 1
#         else:
#             filled_status = True
#             num_of_trades += 1
#         # REVERSAL BE CAREFUL - Buy stock
#         if trade_limit == 4:
#             order_number = evaluate_reverse_trade(data, current_signal, buy_qty, ticker, fast_MA, slow_MA, num_of_signals=5, num_of_checks=20)
#             if order_number:
#                 order_status = Data.print_trade_update(data, ticker, False, False, buy_qty, qty, current_signal, slow_MA, fast_MA, order_number)
#                 if order_status != "filled":
#                     filled_status = attempt_to_fill_order(data, order_number, ticker, current_signal, fast_MA, slow_MA)
#                     if filled_status == True:
#                         num_of_trades += 1
#                 else:
#                     filled_status = True
#                     num_of_trades += 1
#     else:
#         print("No trade executed.")
#         filled_status = False
    
#     return filled_status, num_of_trades



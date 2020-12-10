from config import Alpaca_key,Alpaca_secret_key,Alpaca_endpoint
import alpaca_trade_api as tradeapi

api = tradeapi.REST(Alpaca_key,Alpaca_secret_key,Alpaca_endpoint)

def is_market_open():
    clock = api.get_clock()
    if clock.is_open:
        return True
    else:
        return False

def is_account_blocked():
    account = api.get_account()
    if account.trading_blocked:
        return True
    else:
        return False
    
def is_ticker_owned_already(ticker):
    positions = api.list_positions()
    for position in positions:
        if position.symbol == ticker:
            qty = int(position.qty)
            if qty > 0:
                return True, qty
            elif qty < 0:
                return True, abs(qty)
    return False, 0

def get_buying_power():
    account = api.get_account()
    buying_power = account.buying_power
    return buying_power

def any_open_positions():
    positions = api.list_positions()
    if positions:
        return True     
    else:
        return False
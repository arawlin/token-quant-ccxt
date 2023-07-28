import os
import sys

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from dotenv import load_dotenv

load_dotenv()

import time
import ccxt

from lib import log_object

SYMBOL_BASE = "BTC"
SYMBOL_QUOTE = "USDT"
SYMBOL = SYMBOL_BASE + "/" + SYMBOL_QUOTE + ":USDT"

MARGIN_TYPE = "isolated"
LEVERAGE = 10
SIDE_POSITION = "short"

RATE_VALUE_MID = 0.5
RATE_VALUE_DELTA = 0.0005

MIN_QUANTITY = 0.001

INTERVAL_TICKER = 5
INTERVAL_TICKER_QUICK_RATE = 2
INTERVAL_OPEN_ORDER_WAIT = 2

ex = ccxt.binanceusdm(
    {
        "apiKey": os.getenv("API_KEY"),
        "secret": os.getenv("API_SECRET"),
    }
)
# ex.http_proxy = "http://192.168.1.100:1083/"
ex.https_proxy = "http://192.168.1.100:1083/"
# ex.socks_proxy = "socks5://192.168.1.100:1082/"
# ex.verbose = True

ex.set_margin_mode(MARGIN_TYPE, SYMBOL)
ex.set_leverage(LEVERAGE, SYMBOL)
# ex.set_position_mode(hedged=True, symbol=SYMBOL)

volume_total = 0
interval_ticker_cur = INTERVAL_TICKER  # the interval will be quick when trading


def calc_grid_price(price, rate, num):
    """
    geometric
    """
    prices = []
    p = price
    for i in range(num):
        p *= 1 + rate
        prices.append(p)
    return prices

def calc_grid_quantity(price, rate, amount, num, grids):
    global quaa
    num -= 1
    if num < 0:
        return

    price = price * (1 + rate)

    a = amount * rate / 2
    amount += a

    q = -(a / price)

    grids.append([price, q])
    calc_grid_quantity(price, rate, amount, num, grids)


def update_balance(side_position="long"):
    global volume_total
    global interval_ticker_cur

    try:
        return
    except Exception as e:
        print(e)


if __name__ == "__main__":
    # print(calc_grid_price(1000, 0.01, 10))
    # print(calc_grid_price(1000, -0.01, 10))

    # grids = []
    # calc_grid_quantity(1000, 0.01, 1000, 10, grids)
    # print(len(grids), grids)

    # grids = []
    # calc_grid_quantity(1000, -0.01, 1000, 10, grids)
    # print(grids)

    # while 1:
    #     update_balance(SIDE_POSITION)
    #     time.sleep(interval_ticker_cur)
    #     interval_ticker_cur = INTERVAL_TICKER

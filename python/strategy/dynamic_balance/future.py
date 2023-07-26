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
LEVERAGE = 1
SIDE_POSITION = "long"

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
# ex.https_proxy = "http://192.168.1.100:1083/"
# ex.socks_proxy = "socks5://192.168.1.100:1082/"
# ex.verbose = True

ex.set_margin_mode(MARGIN_TYPE, SYMBOL)
ex.set_leverage(LEVERAGE, SYMBOL)
# ex.set_position_mode(hedged=True, symbol=SYMBOL)

volume_total = 0
interval_ticker_cur = INTERVAL_TICKER  # the interval will be quick when trading


def update_balance(side_position="long"):
    global volume_total
    global interval_ticker_cur

    try:
        positions = ex.fetch_positions([SYMBOL])
        pos = ccxt.Exchange.filter_by(positions, "side", side_position)
        value_base = pos[0]["collateral"] if len(pos) > 0 else 0
        value_base *= LEVERAGE

        balances = ex.fetch_balance()
        bal_free_quote = balances[SYMBOL_QUOTE]["free"]
        value_quote = bal_free_quote * LEVERAGE

        side_order = ""
        val = 0
        rate_value = value_base / (value_base + value_quote)
        if rate_value > RATE_VALUE_MID + RATE_VALUE_DELTA:
            side_order = "sell" if side_position == "long" else "buy"
            val = (value_base - value_quote) / 2
        elif rate_value < RATE_VALUE_MID - RATE_VALUE_DELTA:
            side_order = "buy" if side_position == "long" else "sell"
            val = (value_quote - value_base) / 2

        print(
            f"持仓价值: {value_base}, 可用价值: {value_quote}, 价值比: {rate_value}, 可用余额: {bal_free_quote}, 成交量: {volume_total}"
        )

        if not side_order:
            return
        if val <= 0:
            print(f"平衡量错误 {val}")
            return

        # best price
        order_book = ex.fetch_order_book(SYMBOL, 10)
        if not order_book:
            return
        if len(order_book["bids"]) == 0 or len(order_book["asks"]) == 0:
            return

        price_best = (
            order_book["bids"][0][0]
            if side_order == "buy"
            else order_book["asks"][0][0]
        )
        if not price_best:
            return

        # open order
        qty = val / price_best
        if qty < MIN_QUANTITY:
            return

        print(
            f"价格: {price_best}, 交易量: {qty}, 交易额: {val}, side_order: {side_order}, side_position: {side_position.upper()}"
        )

        info_order = ex.create_order(
            SYMBOL,
            "limit",
            side_order,
            qty,
            price_best,
            {"positionSide": side_position.upper()},
        )

        # cancel all order
        while True:
            time.sleep(INTERVAL_OPEN_ORDER_WAIT)

            res_cancel = ex.cancel_all_orders(SYMBOL)
            if res_cancel["code"] != "200":
                continue

            # filled need be added to the volume_total
            info_order = ex.fetch_order(info_order["id"], SYMBOL)
            volume_total += info_order["filled"] * info_order["price"]

            break

        # XXX the interval will be quick when trading
        interval_ticker_cur = INTERVAL_TICKER / INTERVAL_TICKER_QUICK_RATE

    except Exception as e:
        print(e)


if __name__ == "__main__":
    while 1:
        update_balance(SIDE_POSITION)
        time.sleep(interval_ticker_cur)
        interval_ticker_cur = INTERVAL_TICKER

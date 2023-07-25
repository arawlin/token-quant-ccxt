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

RATE_VALUE_MID = 0.5
RATE_VALUE_DELTA = 0.0005

MIN_QUANTITY = 0.001

INTERVAL_TICKER = 5
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


def update_balance_long():
    global volume_total

    try:
        positions = ex.fetch_positions([SYMBOL])
        pos = ccxt.Exchange.filter_by(positions, "side", "long")
        value_base = pos[0]["notional"] if len(pos) > 0 else 0

        balances = ex.fetch_balance()
        bal_free_quote = balances[SYMBOL_QUOTE]["free"]
        value_quote = bal_free_quote * LEVERAGE

        order_side = 0
        val = 0
        rate_value = value_base / (value_base + value_quote)
        if rate_value > RATE_VALUE_MID + RATE_VALUE_DELTA:
            # sell
            order_side = -1
            val = (value_base - value_quote) / 2
        elif rate_value < RATE_VALUE_MID - RATE_VALUE_DELTA:
            # buy
            order_side = 1
            val = (value_quote - value_base) / 2

        print(
            f"持仓价值: {value_base}, 可用价值: {value_quote}, 价值比: {rate_value}, 可用余额: {bal_free_quote}, 成交量: {volume_total}"
        )

        if order_side == 0:
            return
        if val <= 0:
            print(f"平衡量错误 {val}")
            return

        # best price
        order_book = ex.fetch_order_book(SYMBOL, 10)
        if not order_book:
            return
        if len(order_book["bids"]) == 0:
            return
        price_best = order_book["bids"][0][0]

        # open order
        qty = val / price_best
        if qty < MIN_QUANTITY:
            return

        side = "buy" if order_side > 0 else "sell"
        side_position = "LONG"

        print(
            f"价格: {price_best}, 交易量: {qty}, 交易额: {val}, side: {side}, side_position: {side_position}"
        )

        info_order = ex.create_order(
            SYMBOL, "limit", side, qty, price_best, {"positionSide": side_position}
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

    except Exception as e:
        print(e)


if __name__ == "__main__":
    while 1:
        update_balance_long()
        time.sleep(INTERVAL_TICKER)

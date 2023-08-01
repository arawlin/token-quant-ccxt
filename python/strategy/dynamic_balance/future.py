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
import strategy.common as common

INTERVAL_TICKER = 5
INTERVAL_TICKER_QUICK_RATE = 2
INTERVAL_OPEN_ORDER_WAIT = 2

SYMBOL_BASE = "ETH"
SYMBOL_QUOTE = "USDT"
SYMBOL = SYMBOL_BASE + "/" + SYMBOL_QUOTE + ":USDT"

MARGIN_TYPE = "isolated"
LEVERAGE = 10
SIDE_POSITION = "long"  # long, short

RATE_VALUE_MID = 0.5
RATE_VALUE_DELTA = 0.0005

MIN_QUANTITY = 0.003

RATE_PRICE_GRID = 0.01
NUM_GRID = 2
SYMBOL_SIDE_GRID = ["high", "low"]


volume_total = 0
interval_ticker_cur = INTERVAL_TICKER  # the interval will be quick when trading

# 0: balance
# 1: place
# 2: check
state = 0

old_pos_contracts = 0


def init():
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

    return ex


def update_balance(ex, side_position="long"):
    global volume_total
    global interval_ticker_cur
    global state

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
        else:
            # already balanced
            state = 1

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
            # already balanced
            state = 1
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
        common.cancel_order_all(ex, SYMBOL)

        # filled need be added to the volume_total
        info_order = ex.fetch_order(info_order["id"], SYMBOL)
        volume_total += info_order["filled"] * info_order["price"]

        # XXX the interval will be quick when trading
        interval_ticker_cur = INTERVAL_TICKER / INTERVAL_TICKER_QUICK_RATE

    except Exception as e:
        print(e)


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
    num -= 1
    if num < 0:
        return amount

    price = price * (1 + rate)

    a = amount * rate / 2
    amount += a

    q = -(a / price)

    grids.append([price, q])
    return calc_grid_quantity(price, rate, amount, num, grids)


def place_grids_action(ex, price, value, side_grid="high", side_position="long"):
    grids = []
    rate = RATE_PRICE_GRID if side_grid == "high" else -RATE_PRICE_GRID
    value_need = calc_grid_quantity(price, rate, value, NUM_GRID, grids)
    print(f"grids: {grids}")

    if len(grids) != NUM_GRID:
        print("grids error 1")
        return False
    if value < value_need:
        print(f"grids error 2, value: {value}, value_need: {value_need}")
        return False

    side_order = ""
    if side_grid == "high":
        side_order = "sell" if side_position == "long" else "buy"
    if side_grid == "low":
        side_order = "buy" if side_position == "long" else "sell"
    if not side_grid:
        print("grids error 3")
        return False

    print(
        f"价格:${price}, 所需价值: {value_need}, side_grid: {side_grid}, side_order: {side_order}, side_position: {side_position}"
    )

    for i in grids:
        if i[1] < MIN_QUANTITY:
            print(f"grids error 4, qty: {i[1]} less than MIN_QUANTITY: {MIN_QUANTITY}")
            return False

        ex.create_order(
            SYMBOL,
            "limit",
            side_order,
            i[1],
            i[0],
            {"positionSide": side_position.upper()},
        )

    return True


def place_grids(ex, side_position="long"):
    global state
    try:
        common.cancel_order_all(ex, SYMBOL)

        ticker = ex.fetch_ticker(SYMBOL)
        price = ticker["last"]

        balances = ex.fetch_balance()
        bal_free_quote = balances[SYMBOL_QUOTE]["free"]
        value = bal_free_quote * LEVERAGE

        print(f"state: {state}, price: {price}, value: {value}")

        is_succ_high = place_grids_action(ex, price, value, "high", side_position)
        is_succ_low = place_grids_action(ex, price, value, "low", side_position)

        if not is_succ_high or not is_succ_low:
            return

        # next stage
        state = 2

        print(f"next state: {state}")

    except Exception as e:
        print(e)


def check_balance(ex, side_position="long"):
    global state
    global old_pos_contracts

    try:
        positions = ex.fetch_positions([SYMBOL])
        pos = ccxt.Exchange.filter_by(positions, "side", side_position)
        pos_contracts = pos[0]["contracts"] if len(pos) > 0 else 0

        if old_pos_contracts == 0:
            old_pos_contracts = pos_contracts
            return

        # position would really be changed to more or less when contracts changed
        if pos_contracts == old_pos_contracts:
            return

        # next stage
        state = 0
        old_pos_contracts = 0

        common.cancel_order_all(ex, SYMBOL)

        print(
            f"next state: {state}, pos_contracts: {pos_contracts}, old_pos_contracts: {old_pos_contracts}"
        )

    except Exception as e:
        print(e)


if __name__ == "__main__":
    ex = init()
    common.cancel_order_all(ex, SYMBOL)
    while 1:
        if state == 0:
            update_balance(ex, SIDE_POSITION)
        elif state == 1:
            place_grids(ex, SIDE_POSITION)
        elif state == 2:
            check_balance(ex, SIDE_POSITION)

        time.sleep(interval_ticker_cur)
        interval_ticker_cur = INTERVAL_TICKER

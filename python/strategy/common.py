import time


def cancel_order_all(exchange, symbol, interval=2):
    while True:
        time.sleep(interval)

        res_cancel = exchange.cancel_all_orders(symbol)
        if res_cancel["code"] != "200":
            continue

        break


def market_info(exchange, symbol):
    return exchange.markets[symbol]


def market_info_min_qty(exchange, symbol):
    price = exchange.fetch_ticker(symbol)["last"]

    info = market_info(exchange, symbol)
    limits = info["limits"]
    qty_min = limits["amount"]["min"]
    amt_min = limits["cost"]["min"]
    return max(qty_min, amt_min / price)

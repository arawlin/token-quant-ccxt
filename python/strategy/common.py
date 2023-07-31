import time


def cancel_order_all(exchange, symbol, interval=2):
    while True:
        time.sleep(interval)

        res_cancel = exchange.cancel_all_orders(symbol)
        if res_cancel["code"] != "200":
            continue

        break

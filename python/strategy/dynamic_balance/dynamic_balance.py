import time
import ccxt

SYMBOL_BASE = "BTC"
SYMBOL_QUOTE = "USDT"
SYMBOL = SYMBOL_BASE + "/" + SYMBOL_QUOTE

INTERVAL_TICKER = 10
RATE_VALUE_MID = 0.5
RATE_VALUE_DELTA = 0.0005

ex = ccxt.binanceusdm(
    {
        "apiKey": "0dMzyBDfhO10Q58x5JgMSk95gcZK9HWWdNMLoi68t1UrqpaoodTf5DvZoUMmLH12",
        "secret": "N6Wwuc15Pbc6gD1YisKso4kumrfJJnv26oqx15W1EblBRc0c28ADniuJAu9jQpNG",
    }
)
ex.http_proxy = "http://192.168.1.100:1083/"
ex.https_proxy = "http://192.168.1.100:1083/"
ex.verbose = True


def find_balance():
    bals = ex.fetch_balance()
    print(bals)
    return (
        bals["USDT"]["free"],
        bals["USDT"]["used"],
        bals["USDT"]["total"],
        bals["BTC"]["free"],
        bals["BTC"]["used"],
        bals["BTC"]["total"],
    )


def update_balance():
    try:
        (
            bal_quote_free,
            bal_quote_used,
            bal_quote_total,
            bal_base_free,
            bal_base_used,
            bal_base_total,
        ) = find_balance()

        ticker = ex.fetch_ticker(SYMBOL)
        print(ticker)
        price = ticker.last

        order_direction = 0
        rate_value = bal_base_total * price / (bal_base_total * price + bal_quote_total)
        if rate_value > RATE_VALUE_MID + RATE_VALUE_DELTA:
            # sell
            order_direction = -1
            val = (bal_base_total * price - bal_base_total) / 2
        elif rate_value < RATE_VALUE_MID - RATE_VALUE_DELTA:
            # buy
            order_direction = 1
            val = (bal_base_total - bal_base_total * price) / 2

        if order_direction == 0:
            return

        str_direction = "buy" if order_direction > 0 else "sell"
        ex.create_order(SYMBOL, "limit", str_direction, val, price, {})

    except Exception as e:
        print(e)


if __name__ == "__main__":
    print(ex.fetch("https://api.ipify.org/"))
    update_balance()

    # while 1:
    #     update_balance()
    #     time.sleep(INTERVAL_TICKER)

import random

init_btc_price = 30000
init_sim_times = 1440
btc_price = init_btc_price
free_usdt = 500
free_btc = 0.01667
fee = 0.001
sim_times = 0
total_btc_fee_cost = 0
total_usdt_fee_cost = 0
balance_times = 0
amount_trade = 0

rate_value_delta = 0.0004
rate_price_delta = 0.002


def get_btc_price():
    global btc_price
    global sim_times
    ran = random.randint(0, 1)
    if ran == 0:
        btc_price = btc_price * (1 + rate_price_delta)
    else:
        btc_price = btc_price * (1 - rate_price_delta)
    if sim_times == init_sim_times:
        btc_price = init_btc_price
    return btc_price


def update_balance(initAsset):
    global free_btc
    global free_usdt
    global total_btc_fee_cost
    global total_usdt_fee_cost
    global balance_times
    global sim_times
    global amount_trade
    btc_price = get_btc_price()

    rate_print(free_usdt, free_btc, btc_price)

    p = free_btc * btc_price / ((free_btc * btc_price) + free_usdt)
    if p > 0.5 + rate_value_delta:
        # 出售btc
        sell_value = (free_btc * btc_price - free_usdt) / 2
        sell_btc_amount = sell_value / btc_price
        free_btc = free_btc - sell_btc_amount
        free_usdt = free_usdt + sell_value

        fee_cost = sell_value * fee
        free_usdt = free_usdt - fee_cost  # 扣除手续费
        total_usdt_fee_cost = total_usdt_fee_cost + fee_cost

        amount_trade += sell_value

        balance_times = balance_times + 1
    elif p < 0.5 - rate_value_delta:
        # 购买btc
        buy_value = (free_usdt - free_btc * btc_price) / 2
        buy_btc_amount = buy_value / btc_price
        free_btc = free_btc + buy_btc_amount
        free_usdt = free_usdt - buy_value

        fee_cost = buy_btc_amount * fee
        free_btc = free_btc - fee_cost  # 扣除手续费
        total_btc_fee_cost = total_btc_fee_cost + fee_cost

        amount_trade += buy_value

        balance_times = balance_times + 1
    nowAsset = free_btc * btc_price + free_usdt

    print(
        "btc价格:"
        + str(btc_price)
        + ", 循环次数:"
        + str(sim_times)
        + ", 平衡次数:"
        + str(balance_times)
        + ", 持有btc:"
        + str(free_btc)
        + ", 持有usdt:"
        + str(free_usdt)
        + ", 总价值:"
        + str(nowAsset)
        + ", 盈利:"
        + str(nowAsset - initAsset)
        + ", BTC手续费消耗:"
        + str(total_btc_fee_cost)
        + ", USDT手续费消耗:"
        + str(total_usdt_fee_cost)
        + ", 总成交量:"
        + str(amount_trade)
        + "\n"
    )


def p_r():
    global free_btc
    global free_usdt

    price = get_btc_price()
    print("price:", price, ", ", p(free_usdt, free_btc, price, 0.002))


def p(a, q, p, r=0.002):
    return 1 - (a * (0.5 + r)) / ((0.5 - r) * q * p)


def rate_print(a, q, p):
    print("price:", p, "btc:", q, "u:", a, "rate_value:", r(a, q, p))


def r(a, q, p):
    return (q * p) / (q * p + a) - 0.5


if __name__ == "__main__":
    # trading = Trading(exchange)
    # while 1:
    #     trading.poll()
    initAsset = free_btc * btc_price + free_usdt
    print(
        "持有btc:"
        + str(free_btc)
        + ",持有usdt:"
        + str(free_usdt)
        + ",总价值:"
        + str(initAsset)
    )
    while True:
        update_balance(initAsset)
        sim_times = sim_times + 1
        if sim_times > init_sim_times:
            exit(0)
        # time.sleep(1)

import random

init_btc_price = 30000
init_sim_times = 10000
btc_price = init_btc_price
free_usdt = 30000
free_btc = 1
fee = 0.001
sim_times = 0
total_btc_fee_cost = 0
total_usdt_fee_cost = 0
balance_times = 0

price_fluctuation = 1
value_rate_delt = 0.003

def get_btc_price():
    global btc_price
    global sim_times
    ran = random.randint(0,1)
    if ran == 0:
        btc_price = btc_price + 1
    else:
        btc_price = btc_price - 1
    sim_times = sim_times + 1
    if (sim_times == init_sim_times):
        btc_price = init_btc_price
    return btc_price

def update_balance(initAsset):
    global free_btc
    global free_usdt
    global total_btc_fee_cost
    global total_usdt_fee_cost
    global balance_times
    btc_price = get_btc_price()
    p = free_btc * btc_price / ((free_btc * btc_price) + free_usdt)
    if p > 0.5001:
        # 出售btc
        sell_value = (free_btc*btc_price - free_usdt) / 2
        sell_btc_amount = sell_value / btc_price
        free_btc = free_btc - sell_btc_amount
        free_usdt = free_usdt + sell_value
        
        fee_cost = sell_value * fee
        free_usdt = free_usdt - fee_cost # 扣除手续费
        total_usdt_fee_cost = total_usdt_fee_cost + fee_cost
        
        balance_times = balance_times + 1
    elif p < 0.4999:
        # 购买btc
        buy_value = (free_usdt - free_btc * btc_price) / 2
        buy_btc_amount = buy_value / btc_price
        free_btc = free_btc + buy_btc_amount
        free_usdt = free_usdt - buy_value

        fee_cost = buy_btc_amount * fee
        free_btc = free_btc - fee_cost  # 扣除手续费
        total_btc_fee_cost = total_btc_fee_cost + fee_cost

        balance_times = balance_times + 1
    nowAsset = free_btc*btc_price+free_usdt

    print("平衡次数:"+str(balance_times)+",btc价格:"+str(btc_price)+"持有btc:"+str(free_btc)+",持有usdt:"+str(free_usdt)+",总价值:"+str(nowAsset)+",盈利:"+str(nowAsset-initAsset)+",BTC手续费消耗:"+str(total_btc_fee_cost)+",USDT手续费消耗:"+str(total_usdt_fee_cost) + "\n")
    if sim_times == init_sim_times:
        exit(0)

if __name__ == '__main__':
    # trading = Trading(exchange)
    # while 1:
    #     trading.poll()
    initAsset = free_btc*btc_price+free_usdt
    print("持有btc:"+str(free_btc)+",持有usdt:"+str(free_usdt)+",总价值:"+str(initAsset))
    while True:
        update_balance(initAsset)
        # time.sleep(1)
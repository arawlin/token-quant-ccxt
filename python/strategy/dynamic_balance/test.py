import os
import sys
import time
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(root + '/python')
import ccxt

exchange = ccxt.binance ({
    'apiKey': '6hybk6cBoueRQSgfuHwJ7ZazPt9Kk7GirvuoUYL1AtbNRBxwpfVFobp6Ce1ZSgQe',
    'secret': 'ttE2H0LvMpNvkRWc2x9KZ4hwTI2WEZK0bBIPkWXlZgVyKffmzb4c3k0bvyrpPzEF',
})

TickInterval = 280
BurstThresholdPct = 0.00005
BurstThresholdVol = 10
Symbol = "BTC/USDT" 
BalanceTimeout = 10000/1000     # 平衡等代时间(毫秒)
MinStock = 0.001

def findBalance():
    try:
        kk = exchange.fetch_balance()
        if kk:
            print("我持有的USDT:{}".format(kk['USDT']))
            print("我持有的BTC:{}".format(kk['BTC']))
            return kk['USDT']['free'], kk['USDT']['used'], kk['USDT']['total'],kk['BTC']['free'],kk['BTC']['used'],kk['BTC']['total']
        else:
            0,0,0
    except Exception as e:
        print(e)

class Trading:
    def __init__(self, exchange):
        self.exchange = exchange
        self.prices = []         
        self.orderBook = {}         # 订单薄
        self.vol = 0                # 当个tick的成交量
        self.lastTradeId = 0        
        self.bidPrice = 0           
        self.askPrice = 0
        self.p = 0.5
        self.tradeOrderId = 0
        self.trading = False
        self.usdt = 0
        self.btc = 0
        self.numTick = 0
        

     #获取最新成交记录的价格和成交量
    def updateTrades(self):
        trades = self.exchange.fetch_trades(Symbol)                             
        if (len(self.prices)== 0):                                              
            while (len(trades) == 0):                                           
                trades = self.exchange.fetch_trades(Symbol)                
            for i in range(15):                                                
                self.prices.append(trades[-i]['price'])                         

        tradesvol = 0
        for trade in trades:
            if ((int(trade['id']) > self.lastTradeId) or (int(trade['id']) == 0 and trade['timestamp'] > self.lastTradeId)):
                #等号右边是一个三目运算，如果trade.Id=0就返回trade.Time，否则就返回trade.Id, self.lastTradeId。并进行比较返回最大的值，最后把返回的最大值赋给self.lastTradeId
                temp = trade['timestamp'] if int(trade['id']) == 0 else int(trade['id'])
                self.lastTradeId = max(temp, self.lastTradeId)
                tradesvol = tradesvol + trade['amount']
        # 本次tick交易量 = 上次tick交易量*0.7 + 本次tick期间实际发生的交易量*0.3，用于平滑和减少噪音
        self.vol = 0.7 * self.vol + 0.3 * tradesvol
    
    def updateOrderBook(self):
        orderBook = self.exchange.fetch_order_book(Symbol)
        self.orderBook = orderBook 
        if (len(orderBook['bids'])< 3 or len(orderBook['asks']) < 3):
            return
        self.bidPrice = orderBook['bids'][0][0] * 0.618 + orderBook['asks'][0][0] * 0.382 + 0.01
        self.askPrice = orderBook['bids'][0][0] * 0.382 + orderBook['asks'][0][0] * 0.618 - 0.01

        # 本次tick价格 = (买1+卖1)*0.35 + (买2+卖2) * 0.10 + (买3+卖3)*0.05
        del(self.prices[0])
        tmp =   (orderBook['bids'][0][0]+orderBook['asks'][0][0])/2*0.7+ \
                (orderBook['bids'][1][0]+orderBook['asks'][1][0])/2*0.2+ \
                (orderBook['bids'][2][0]+orderBook['asks'][2][0])/2*0.1
        self.prices.append(tmp)

    # btc:521 usdt:479  卖30刀  491  509
    def updateBalance(self):
        if self.trading:
            return
        t = time.time()
        # 这里有一个仓位平衡的辅助策略
        # 仓位平衡策略是在仓位偏离50%时，通过不断提交小单来使仓位回归50%的策略，
        # 这个辅助策略可以有效减少趋势策略中趋势反转+大滑点带来的大幅回撤
        usdt_free,usdt_used,usdt_total,btc_free,btc_used,btc_total =  findBalance()
        if usdt_total is None:
            return
        self.usdt = usdt_free
        self.btc = btc_free
        self.p = btc_free * self.prices[-1] / (btc_free * self.prices[-1] + usdt_free)
        if self.p < 0.48 and len(self.orderBook['bids']) > 0:       # 开始购买
            params = {}
            price = self.orderBook['bids'][0][0]
            amount = 0.001
            self.exchange.create_order(Symbol, 'limit', 'buy', amount, price + 0.00, params)
            self.exchange.create_order(Symbol, 'limit', 'buy', amount, price + 0.01, params)
            self.exchange.create_order(Symbol, 'limit', 'buy', amount, price + 0.02, params)
        elif self.p > 0.52 and len(self.orderBook['asks']) > 0:     # 开始出售
            params = {}
            price = self.orderBook['asks'][0][0]
            amount = 0.001
            self.exchange.create_order(Symbol, 'limit', 'sell', amount, price - 0.00, params)
            self.exchange.create_order(Symbol, 'limit', 'sell', amount, price - 0.01, params)
            self.exchange.create_order(Symbol, 'limit', 'sell', amount, price - 0.02, params)

        time.sleep(BalanceTimeout)
        orders = self.exchange.fetch_open_orders(Symbol)
        if (orders):
            for i in range(len(orders)):
                self.exchange.cancel_order(orders[i]["id"], Symbol)


    def poll(self):
        self.numTick += 1
        self.trading = False
        self.updateTrades()
        self.updateOrderBook()
        self.updateBalance()

        burstPrice = self.prices[-1] * BurstThresholdPct
        bull = False
        bear = False
        tradeAmount = 0
        
        # 趋势策略，价格出现方向上的突破时开始交易
        if (self.numTick > 2 and ((self.prices[-1] - max(self.prices[-6:-2]) > burstPrice) or (self.prices[-1] - max(self.prices[-6:-3]) > burstPrice and self.prices[-1] > self.prices[-2]))):
            bull = True
            tradeAmount = self.usdt / self.bidPrice * 0.99
        elif (self.numTick > 2 and ((self.prices[-1] - min(self.prices[-6:-2]) < -burstPrice) or (self.prices[-1] - min(self.prices[-6:-3]) < -burstPrice and self.prices[-1] < self.prices[-2]))):
            bear = True
            tradeAmount = self.btc

        #  下单力度计算
        #  1. 小成交量的趋势成功率比较低，减小力度
        #  2. 过度频繁交易有害，减小力度
        #  3. 短时价格波动过大，减小力度
        #  4. 盘口价差过大，减少力度
        if (self.vol < BurstThresholdVol):
            tradeAmount *= self.vol / BurstThresholdVol
        if (self.numTick < 5):
            tradeAmount *= 0.8
        if (self.numTick < 10):
            tradeAmount *= 0.8

        if (bull and self.prices[-1] < max(self.prices)):
            tradeAmount *= 0.90
        if (bear and self.prices[-1] > min(self.prices)):
            tradeAmount *= 0.90
        if (abs(self.prices[-1] - self.prices[-2]) > burstPrice * 2):
            tradeAmount *= 0.90
        if (abs(self.prices[-1] - self.prices[-2]) > burstPrice * 3):
            tradeAmount *= 0.90
        if (abs(self.prices[-1] - self.prices[-2]) > burstPrice * 4):
            tradeAmount *= 0.90
        if (self.orderBook['asks'][0][0] - self.orderBook['bids'][0][0] > burstPrice * 2):
            tradeAmount *= 0.90
        if (self.orderBook['asks'][0][0] - self.orderBook['bids'][0][0] > burstPrice * 3):
            tradeAmount *= 0.90
        if (self.orderBook['asks'][0][0] - self.orderBook['bids'][0][0] > burstPrice * 4):
            tradeAmount *= 0.90

        if (tradeAmount >= MinStock):   # 最后下单量小于MinStock的就不操作了
            tradePrice = self.bidPrice if bull else self.askPrice
            self.trading = True
            while (tradeAmount >= MinStock):
                p3 = None
                if bull:
                    self.exchange.create_order(symbol=Symbol, side='buy', type="limit",price=self.orderBook['bids'][0][0],amount=tradeAmount)
                else:
                    self.exchange.create_order(symbol=Symbol, side='sell', type="limit",price=self.orderBook['asks'][0][0],amount=tradeAmount)
                orderId =  p3['info']['orderId']
                time.sleep(0.2)
                # 撤销订单
                try:
                    self.exchange.cancel_order(orderId, Symbol)
                except Exception as e:
                    print(e)   

                order = self.exchange.fetch_order(orderId, Symbol)
                tradeAmount -= order["filled"]
                tradeAmount -= 0.01
                tradeAmount *= 0.98  #每轮循环都少量削减力度

                s2 = self.exchange.fetch_order_status(orderId,  symbol=Symbol)
                if s2 == 'canceled':
                    self.updateOrderBook()  # 更新盘口，更新后的价格高于提单价格也需要削减力度
                    while (bull and self.bidPrice - tradePrice > 0.1):
                        tradeAmount *= 0.99
                        tradePrice += 0.1

                    while (bear and self.askPrice - tradePrice < -0.1):
                        tradeAmount *= 0.99
                        tradePrice -= 0.1

            self.numTick = 0

if __name__ == '__main__':
    trading = Trading(exchange)
    while 1:
        trading.poll()


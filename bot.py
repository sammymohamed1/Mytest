import time
from binance.client import Client
from binance.enums import *
from numpy import *
import math
import datetime
import pandas as pd 
import numpy as np
import keys


TRADE_SYMBOL = 'XRPUSDT'


client = Client(keys.API_KEY, keys.API_SECRET)






# b= balance['free'] 
 
# print(b)
# order = client.order_market_buy(symbol='BTCUSDT', quantity=(float(quantity))) 
# orders = client.get_open_orders(symbol='BTCUSDT') 
# print(orders)



in_position = False

firstRun = True
makeTrade = False

state = 0
prevTime = 0

data = []
signals = []

buyPrice = 0
bestPrice = 0
sinceBest = 0

sellToBuyTransition = False

hasToken = False


def emaPoints(data, dataPoints):
    ema1 = []
    
    for i in range(len(data)):
        ema = 0
        if i > 0:
            prevEma = ema1[i-1]
            multiplyer = 2/(dataPoints+1)
            ema = (float(data[i][4]) - prevEma)*multiplyer+prevEma

        ema1.append(ema)
    return ema1

def emaPointsMacd(data, dataPoints):
    ema1 = []
    
    for i in range(len(data)):
        ema = 0
        if i > 0:
            prevEma = ema1[i-1]
            multiplyer = 2/(dataPoints+1)
            ema = (data[i] - prevEma)*multiplyer+prevEma

        ema1.append(ema)
    return ema1

def macd(data):

    ema12 = emaPoints(data,12)
    ema26 = emaPoints(data,26)
    macd = []
    for i in range(len(ema12)):
        m = ema12[i]-ema26[i]
        macd.append(m)
    
    signal = emaPointsMacd(macd,9) 
    
    return macd, signal
#%%
def makeTrainingData(data):
    
    macda, signal = macd(data)
    
    features = []
    
    for i in range(100,len(data)):
        
        #x = [macda[i], signal[i]]
        x = [macda[i], signal[i]]
        features.append(x)
    return features

def getCoinBalance(client, currency):
    balance = float(client.get_asset_balance(asset=currency)['free'])
    return balance

def round_decimals_down(number:float, decimals:int=2):
    """
    Returns a value rounded down to a specific number of decimal places.
    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more")
    elif decimals == 0:
        return math.floor(number)

    factor = 10 ** decimals
    return math.floor(number * factor) / factor

def sell():
    balance = client.get_asset_balance(asset='xrp')

    b = float(balance['free'])

    roundD = round_decimals_down(b, 2)

    print(roundD)



    try:
        print("sending order")
        order = client.order_market_sell(
            symbol=TRADE_SYMBOL,
            quantity=roundD
        )
        print("Trading Pair = ", order['symbol'])
        print ("status = ", order['status'])
        print("quantity = ", order[{'qty'}])
    except Exception as e:
        print("an exception occured - {}".format(e))


def buy():
    
    balance = client.get_asset_balance(asset='USDT')

    b = float(balance['free'])

    roundD = round_decimals_down(b, 2)

    print(roundD)



    try:
        print("sending order")
        order = client.order_market_buy(
            symbol=TRADE_SYMBOL,
            quantity=roundD
        )
        print("Trading Pair = ", order['symbol'])
        print ("status = ", order['status'])
        print("quantity = ", order[{'qty'}])
    except Exception as e:
        print("an exception occured - {}".format(e))


while(True):
    
    if state == 0:
        
        candles = client.get_klines(symbol=TRADE_SYMBOL, interval=Client.KLINE_INTERVAL_3MINUTE)
        
        if firstRun == True:
            prevTime = datetime.datetime.fromtimestamp(candles[498][0]/ 1e3)
            
            firstRun = False
            makeTrade = True
            
            for i in range(499):
                data.append(candles[i])
            
        else: 

            currTime = datetime.datetime.fromtimestamp(candles[498][0]/ 1e3)
            
            if prevTime != currTime:
                data.append(candles[498])
                prevTime = currTime
                makeTrade = True
                if makeTrade == True:
                    print("Market is ready to buy")

            else:
                
                makeTrade = False
                if makeTrade == False:
                    print("The market is still not in position")
                       
        

        if makeTrade == True:
            state = 1
            makeTrade = False
        #if its not then look for early selling opporunity to cash in profits
        else:
            
            if hasToken == True:
                try:
                    
                    prices =  client.get_order_book(symbol=TRADE_SYMBOL)
                    price = prices['bids'][0][0]
                    
                    if float(price) > float(bestPrice):
                        
                        bestPrice = price
                        sinceBest = 0
                    else:
                        sinceBest = sinceBest + 1
                    
                    if (float(price)/float(buyPrice))>1.001 and sinceBest >= 2:
                        
                        print("Selling")
                        
                        sell()

                        hasToken = False
                        sellToBuyTransition = False
                        buyPrice = 0
                        bestPrice = 0
                        sinceBest = 0
                        currentxrp = getCoinBalance(client, 'xrp') 
                    else:
                        print("")

                except Exception as e:
                    print(e)
        
            time.sleep(1)

    #make signals data used for the strategy
    if state == 1:
        signals = makeTrainingData(data)
        print(1)
        state = 2

    if state == 2:
        currentxrp = getCoinBalance(client, 'xrp') 
        state = 3
        
    if state == 3:
        current = signals[len(signals)-1]
        
        if current[0] > current[1]:
            print("Buy Signal")
                
            if hasToken == False and sellToBuyTransition == True:
                try:
                    print("Buying")
                    currentxrp = getCoinBalance(client, 'xrp') 
                    
                    prices =  client.get_order_book(symbol=TRADE_SYMBOL)
                    price = prices['asks'][0][0]
                    buyPrice = price
                
                    
                    buy()
                    
                    hasToken = True
                    
                    state = 0
                    time.sleep(1)
                        
                except Exception as e:
                    print(e)
            else:
                state = 0
                time.sleep(1)

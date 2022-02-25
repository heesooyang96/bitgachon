import time
import pyupbit
import datetime

access = "ue67fMbyeXuaSU2LpdEmMxNgFMqqPcsDWEALoVMB"
secret = "alSiNsZv0wEtlxlQoPWz6beutKahN4N2HJ6S4oqy"

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_ma10(ticker):
    """10일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=10)
    ma10 = df['close'].rolling(10).mean().iloc[-1]
    return ma10

def get_ma20(ticker):
    """20일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=20)
    ma20 = df['close'].rolling(20).mean().iloc[-1]
    return ma20

def get_ma30(ticker):
    """30일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=30)
    ma30 = df['close'].rolling(30).mean().iloc[-1]
    return ma30

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
balance=get_balance("KRW")
print (balance)
# 자동매매 시작

while True:
    try:
        current_price = get_current_price("KRW-ETH")
        ma10=get_ma10("KRW-ETH")
        ma20=get_ma20("KRW-ETH")
        ma30=get_ma30("KRW-ETH")
        if ma10 > ma20 and current_price > ma20:
            print("Golden Cross observed")
            if krw > 5000:
                print("Now is 59bun and Golden Cross appeared so...")
                upbit.buy_market_order("KRW-ETH", krw*0.995)
                current_price = get_current_price("KRW-ETH")
                krw = get_balance("KRW")
                eth = get_balance("KRW-ETH")
                print("Bought Your Asset!")
                print("Golden Cross occurred:",current_price)
                print("MA10 is:",ma10)
                print("MA20 is:",ma20)
                print("Now Your balance and amount of asset is:",krw,eth)
        if current_price < ma20 :
            print("Dead Cross obeserved")
            print("Now is 59bun and Dead Cross appeared so...")
            current_price = get_current_price("KRW-ETH")
            krw = get_balance("KRW")
            eth = get_balance("ETH")
            print("MA10 is:",ma10)
            print("MA20 is:",ma20)
            print("Dead Cross now:",current_price)
            print("Now Your balance and amount of asset is:",krw,eth)
            if eth > 0.002:
                upbit.sell_market_order("KRW-ETH", eth*0.995)
                print("Sold your Asset!")
        time.sleep(86400)
    except Exception as e:
        print(e)
        time.sleep(86400)
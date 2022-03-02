import time
import pyupbit
import datetime
import pandas
from numpy import nan as npNaN
from pandas import DataFrame, Series
from pandas_ta.utils import get_offset, verify_series, zero
import math

access = "ue67fMbyeXuaSU2LpdEmMxNgFMqqPcsDWEALoVMB"
secret = "alSiNsZv0wEtlxlQoPWz6beutKahN4N2HJ6S4oqy"


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

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

def psar(high, low, close=None, af0=None, af=None, max_af=None, offset=None, **kwargs):
    """Indicator: Parabolic Stop and Reverse (PSAR)"""
    # Validate Arguments
    high = verify_series(high)
    low = verify_series(low)
    af = float(af) if af and af > 0 else 0.02
    af0 = float(af0) if af0 and af0 > 0 else af
    max_af = float(max_af) if max_af and max_af > 0 else 0.2
    offset = get_offset(offset)

    def _falling(high, low, drift:int=1):
        """Returns the last -DM value"""
        # Not to be confused with ta.falling()
        up = high - high.shift(drift)
        dn = low.shift(drift) - low
        _dmn = (((dn > up) & (dn > 0)) * dn).apply(zero).iloc[-1]
        return _dmn > 0

    # Falling if the first NaN -DM is positive
    falling = _falling(high.iloc[:2], low.iloc[:2])
    if falling:
        sar = high.iloc[0]
        ep = low.iloc[0]
    else:
        sar = low.iloc[0]
        ep = high.iloc[0]

    if close is not None:
        close = verify_series(close)
        sar = close.iloc[0]

    long = Series(npNaN, index=high.index)
    short = long.copy()
    reversal = Series(0, index=high.index)
    _af = long.copy()
    _af.iloc[0:2] = af0

    # Calculate Result
    m = high.shape[0]
    for row in range(1, m):
        high_ = high.iloc[row]
        low_ = low.iloc[row]

        if falling:
            _sar = sar + af * (ep - sar)
            reverse = high_ > _sar

            if low_ < ep:
                ep = low_
                af = min(af + af0, max_af)

            _sar = max(high.iloc[row - 1], high.iloc[row - 2], _sar)
        else:
            _sar = sar + af * (ep - sar)
            reverse = low_ < _sar

            if high_ > ep:
                ep = high_
                af = min(af + af0, max_af)

            _sar = min(low.iloc[row - 1], low.iloc[row - 2], _sar)

        if reverse:
            _sar = ep
            af = af0
            falling = not falling # Must come before next line
            ep = low_ if falling else high_

        sar = _sar # Update SAR

        # Seperate long/short sar based on falling
        if falling:
            short.iloc[row] = sar
        else:
            long.iloc[row] = sar

        _af.iloc[row] = af
        reversal.iloc[row] = int(reverse)

    # Offset
    if offset != 0:
        _af = _af.shift(offset)
        long = long.shift(offset)
        short = short.shift(offset)
        reversal = reversal.shift(offset)

    # Handle fills
    if "fillna" in kwargs:
        _af.fillna(kwargs["fillna"], inplace=True)
        long.fillna(kwargs["fillna"], inplace=True)
        short.fillna(kwargs["fillna"], inplace=True)
        reversal.fillna(kwargs["fillna"], inplace=True)
    if "fill_method" in kwargs:
        _af.fillna(method=kwargs["fill_method"], inplace=True)
        long.fillna(method=kwargs["fill_method"], inplace=True)
        short.fillna(method=kwargs["fill_method"], inplace=True)
        reversal.fillna(method=kwargs["fill_method"], inplace=True)

    # Prepare DataFrame to return
    _params = f"_{af0}_{max_af}"
    data = {
        f"PSARl{_params}": long,
        f"PSARs{_params}": short,
        f"PSARaf{_params}": _af,
        f"PSARr{_params}": reversal,
    }
    psardf = DataFrame(data)
    psardf.name = f"PSAR{_params}"
    psardf.category = long.category = short.category = "trend"

    return psardf

def rsi(ohlc: pandas.DataFrame, period: int = 14): 
    delta = ohlc["close"].diff()
    ups, downs = delta.copy(), delta.copy()
    ups[ups < 0] = 0
    downs[downs > 0] = 0 
    AU = ups.ewm(com = period-1, min_periods = period).mean()
    AD = downs.abs().ewm(com = period-1, min_periods = period).mean()
    RS = AU/AD
    
    return pandas.Series(100 - (100/(1 + RS)), name = "RSI")

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

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
balance=get_balance("KRW")
print (balance)
# 자동매매 시작
while True:
    try:
        current_price = get_current_price("KRW-ETH")
        df = pyupbit.get_ohlcv("KRW-ETH", interval="minute5", count=1000)
        nowrsi = rsi(df, 14).iloc[-1]
        df['openhi'] = (df['open'].shift(1) + df['close'].shift(1))/2
        openhi = df['openhi'].iloc[-1]
        df['closehi'] = (df['open']+df['close']+df['low']+df['high'])/4
        closehi = df['closehi'].iloc[-1]
        df['ema200'] = df['closehi'].ewm(200).mean()
        ema200 = df['ema200'].iloc[-1]
        df['psar'] = psar(high=df['high'], low=df['low'], close=df['closehi'], af0=0.02, af=0.02, max_af=0.2).iloc[:,0]
        df = df.fillna(0)
        nowpsar = df['psar'].iloc[-1]
        krw = get_balance("KRW")
        now = datetime.datetime.now()
        print('5분봉 시작',now)
        if closehi > ema200 and nowrsi > 50 and nowpsar > 0:
            krw = get_balance("KRW")
            print('매수조건 충족', now)
            if krw > 5000:
                upbit.buy_market_order("KRW-ETH", krw*0.999)               
                current_price = get_current_price("KRW-ETH")
                print('매수완료', current_price)
        if nowpsar == 0:
            eth = upbit.get_balance("KRW-ETH")
            print('매도조건 충족', now)
            if eth > 0.001:
                upbit.sell_market_order("KRW-ETH", eth*0.999)
                current_price = get_current_price("KRW-ETH")
                print("매도완료", current_price)
        time.sleep(299)
    except Exception as e:
        print(e)
        time.sleep(299)


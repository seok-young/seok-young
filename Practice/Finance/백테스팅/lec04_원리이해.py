# IMPORTING PACKAGES

import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np
from math import floor
from termcolor import colored as cl

plt.style.use('fivethirtyeight')
plt.rcParams['figure.figsize'] = (20, 10)


# EXTRACTING STOCK DATA

def get_historical_data(symbol, start_date):
    api_key = 'YOUR API KEY'
    api_url = f'https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=5000&apikey={api_key}'
    raw_df = requests.get(api_url).json()
    print(raw_df)
    df = pd.DataFrame(raw_df['values']).iloc[::-1].set_index('datetime').astype(float)
    df = df[df.index >= start_date]
    df.index = pd.to_datetime(df.index)
    return df


aapl = get_historical_data('AAPL', '2019-01-01')
aapl.tail()


# TRUE STRENGTH INDEX CALCULATION

def get_tsi(close, long, short, signal):
    diff = close - close.shift(1)
    abs_diff = abs(diff)

    diff_smoothed = diff.ewm(span=long, adjust=False).mean()
    diff_double_smoothed = diff_smoothed.ewm(span=short, adjust=False).mean()
    abs_diff_smoothed = abs_diff.ewm(span=long, adjust=False).mean()
    abs_diff_double_smoothed = abs_diff_smoothed.ewm(span=short, adjust=False).mean()

    tsi = (diff_double_smoothed / abs_diff_double_smoothed) * 100
    signal = tsi.ewm(span=signal, adjust=False).mean()
    tsi = tsi[tsi.index >= '2020-01-01'].dropna()
    signal = signal[signal.index >= '2020-01-01'].dropna()

    return tsi, signal


aapl['tsi'], aapl['signal_line'] = get_tsi(aapl['close'], 25, 13, 12)
aapl = aapl[aapl.index >= '2020-01-01']
aapl.tail()

# TRUE STRENGTH INDEX PLOT

ax1 = plt.subplot2grid((11, 1), (0, 0), rowspan=5, colspan=1)
ax2 = plt.subplot2grid((11, 1), (6, 0), rowspan=5, colspan=1)
ax1.plot(aapl['close'], linewidth=2.5)
ax1.set_title('AAPL CLOSING PRICE')
ax2.plot(aapl['tsi'], linewidth=2, color='orange', label='TSI LINE')
ax2.plot(aapl['signal_line'], linewidth=2, color='#FF006E', label='SIGNAL LINE')
ax2.set_title('AAPL TSI 25,13,12')
ax2.legend()
plt.show()


# TRUE STRENGTH INDEX STRATEGY

def implement_tsi_strategy(prices, tsi, signal_line):
    buy_price = []
    sell_price = []
    tsi_signal = []
    signal = 0

    for i in range(len(prices)):
        if tsi[i - 1] < signal_line[i - 1] and tsi[i] > signal_line[i]:
            if signal != 1:
                buy_price.append(prices[i])
                sell_price.append(np.nan)
                signal = 1
                tsi_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                tsi_signal.append(0)
        elif tsi[i - 1] > signal_line[i - 1] and tsi[i] < signal_line[i]:
            if signal != -1:
                buy_price.append(np.nan)
                sell_price.append(prices[i])
                signal = -1
                tsi_signal.append(signal)
            else:
                buy_price.append(np.nan)
                sell_price.append(np.nan)
                tsi_signal.append(0)
        else:
            buy_price.append(np.nan)
            sell_price.append(np.nan)
            tsi_signal.append(0)

    return buy_price, sell_price, tsi_signal


buy_price, sell_price, tsi_signal = implement_tsi_strategy(aapl['close'], aapl['tsi'], aapl['signal_line'])

# TRUE STRENGTH INDEX TRADING SIGNALS PLOT

ax1 = plt.subplot2grid((11, 1), (0, 0), rowspan=5, colspan=1)
ax2 = plt.subplot2grid((11, 1), (6, 0), rowspan=5, colspan=1)
ax1.plot(aapl['close'], linewidth=2)
ax1.plot(aapl.index, buy_price, marker='^', markersize=12, color='green', linewidth=0, label='BUY SIGNAL')
ax1.plot(aapl.index, sell_price, marker='v', markersize=12, color='r', linewidth=0, label='SELL SIGNAL')
ax1.legend()
ax1.set_title('AAPL TSI TRADING SIGNALS')
ax2.plot(aapl['tsi'], linewidth=2, color='orange', label='TSI LINE')
ax2.plot(aapl['signal_line'], linewidth=2, color='#FF006E', label='SIGNAL LINE')
ax2.set_title('AAPL TSI 25,13,12')
ax2.legend()
plt.show()

# STOCK POSITION

position = []
for i in range(len(tsi_signal)):
    if tsi_signal[i] > 1:
        position.append(0)
    else:
        position.append(1)

for i in range(len(aapl['close'])):
    if tsi_signal[i] == 1:
        position[i] = 1
    elif tsi_signal[i] == -1:
        position[i] = 0
    else:
        position[i] = position[i - 1]

close_price = aapl['close']
tsi = aapl['tsi']
signal_line = aapl['signal_line']
tsi_signal = pd.DataFrame(tsi_signal).rename(columns={0: 'tsi_signal'}).set_index(aapl.index)
position = pd.DataFrame(position).rename(columns={0: 'tsi_position'}).set_index(aapl.index)

frames = [close_price, tsi, signal_line, tsi_signal, position]
strategy = pd.concat(frames, join='inner', axis=1)

strategy
strategy[12:17]

# BACKTESTING

aapl_ret = pd.DataFrame(np.diff(aapl['close'])).rename(columns={0: 'returns'})
tsi_strategy_ret = []

for i in range(len(aapl_ret)):
    returns = aapl_ret['returns'][i] * strategy['tsi_position'][i]
    tsi_strategy_ret.append(returns)

tsi_strategy_ret_df = pd.DataFrame(tsi_strategy_ret).rename(columns={0: 'tsi_returns'})
investment_value = 100000
number_of_stocks = floor(investment_value / aapl['close'][0])
tsi_investment_ret = []

for i in range(len(tsi_strategy_ret_df['tsi_returns'])):
    returns = number_of_stocks * tsi_strategy_ret_df['tsi_returns'][i]
    tsi_investment_ret.append(returns)

tsi_investment_ret_df = pd.DataFrame(tsi_investment_ret).rename(columns={0: 'investment_returns'})
total_investment_ret = round(sum(tsi_investment_ret_df['investment_returns']), 2)
profit_percentage = floor((total_investment_ret / investment_value) * 100)
print(cl('Profit gained from the tsi strategy by investing $100k in AAPL : {}'.format(total_investment_ret),
         attrs=['bold']))
print(cl('Profit percentage of the tsi strategy : {}%'.format(profit_percentage), attrs=['bold']))


# SPY ETF COMPARISON

def get_benchmark(start_date, investment_value):
    spy = get_historical_data('SPY', start_date)['close']
    benchmark = pd.DataFrame(np.diff(spy)).rename(columns={0: 'benchmark_returns'})

    investment_value = investment_value
    number_of_stocks = floor(investment_value / spy[-1])
    benchmark_investment_ret = []

    for i in range(len(benchmark['benchmark_returns'])):
        returns = number_of_stocks * benchmark['benchmark_returns'][i]
        benchmark_investment_ret.append(returns)

    benchmark_investment_ret_df = pd.DataFrame(benchmark_investment_ret).rename(columns={0: 'investment_returns'})
    return benchmark_investment_ret_df


benchmark = get_benchmark('2020-01-01', 100000)
investment_value = 100000
total_benchmark_investment_ret = round(sum(benchmark['investment_returns']), 2)
benchmark_profit_percentage = floor((total_benchmark_investment_ret / investment_value) * 100)
print(cl('Benchmark profit by investing $100k : {}'.format(total_benchmark_investment_ret), attrs=['bold']))
print(cl('Benchmark Profit percentage : {}%'.format(benchmark_profit_percentage), attrs=['bold']))
print(cl('TSI Strategy profit is {}% higher than the Benchmark Profit'.format(
    profit_percentage - benchmark_profit_percentage), attrs=['bold']))
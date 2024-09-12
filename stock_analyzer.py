"""

    This is to be the New and Improved Stock Predictor based off yfinance instead of API calls.

    The intention is to have the ability to:

            - Show 5 year data on individual graphs with average lines for each year to show highs and lows
            - Full 5 year data on one graph (maybe interactive if possible)
            - Comparison of multiple stocks 5 year data (individual graphs and layered?)
            - Comparison of multiple stocks individual years layered over eachother with increasing alpha per stock

    """
import pandas as pd
import yfinance as yf

amd = yf.Ticker('amd')

amd_df = amd.history('5y', '1d')
print(len(amd_df))
import json
import requests
import datetime
import time

import pandas as pd
from matplotlib import pyplot as plt
from decouple import config

class HistoricalData:
    """Class to manage the raw data from RapidAPI into a useable pandas dataframe"""

    url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-chart"
    API_KEY= config("API_KEY")
    headers = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com"
            }
    
    def __init__(self, ticker):
        """Initialize the instance variable for each stock."""
        self.ticker = ticker.upper()
        self.querystring = {"interval":"1d","region":"US","symbol":self.ticker,"range":"5y","events":"split"}
        self.api_response = self._get_api_response()
        self.full_df = self._convert_json_to_pd()
    
    def __repr__(self):
        """Returns the ticker as the name"""
        return self.ticker
    
    def _get_api_response(self):
        """Call the data from rapidAPI, returns the raw dictionary"""
        r = requests.get(self.url, headers=self.headers, params=self.querystring)
        return r.json()

    def _convert_json_to_pd(self):
        """Returns a pandas dataframe with columns date, open, close, high, low, volume, avg."""
        dict_to_pd = {
                    'date': [value for value in self.api_response['chart']['result'][0]['timestamp']],
                    'open': [value for value in self.api_response['chart']['result'][0]['indicators']['quote'][0]['open']],
                    'close': [value for value in self.api_response['chart']['result'][0]['indicators']['quote'][0]['close']],
                    'high': [value for value in self.api_response['chart']['result'][0]['indicators']['quote'][0]['high']],
                    'low': [value for value in self.api_response['chart']['result'][0]['indicators']['quote'][0]['low']],
                    'volume': [value for value in self.api_response['chart']['result'][0]['indicators']['quote'][0]['volume']],
                    }
        df = pd.DataFrame(dict_to_pd)
        df['avg'] = (df.open + df.close) / 2
        df['date'] = df.date.apply(lambda x: datetime.datetime.fromtimestamp(x, datetime.UTC))
        return df

class YearlyData:
    """Class to manage the yearly data of a single stock"""

    def __init__(self, stock):
        """Initialize the instance variables for yearly data functions."""
        self.stock = stock

    def weekly_avg_by_year(self):
        """Create a plot for weekly averages by year"""
        fig, ax = plt.subplots()
        stock_df = self.stock.full_df
        stock_df['year'] = stock_df.date.apply(lambda x: x.strftime('%Y'))
        stock_df['month'] = stock_df.date.apply(lambda x: x.strftime('%m'))
        stock_df['week'] = stock_df.date.apply(lambda x: x.strftime('%U'))
        stock_grouped = stock_df.groupby(['year', 'month', 'week']).avg.mean().reset_index()
        stock_grouped.sort_values(['year', 'month'], ascending=[False, True], inplace=True)
        stock_grouped['month'] = stock_grouped.month.apply(lambda x: datetime.datetime.strptime(x, '%m').strftime('%B'))
        years = stock_grouped['year'].unique()
        for year in years:
            yearly = stock_grouped[stock_grouped.year == year]
            ax.plot(yearly.week, yearly.avg, label=year)
            ax.legend(bbox_to_anchor=(1, 0.85))
            ax.set_title(self.stock)
        plt.show()

    def five_year_full(self):
        """Create a plot for 5 year data from beginning to current."""
        fig, ax = plt.subplots()
        stock_df = self.stock.full_df
        stock_df['year_week'] = stock_df.date.apply(lambda x: x.strftime('%Y %U'))
        grouped_df = stock_df.groupby(['year_week']).avg.mean().reset_index()
        ax.plot(grouped_df.year_week, grouped_df.avg)
        ax.set_title(self.stock)
        plt.xticks(rotation=45)
        plt.show()
            
    def yearly_with_avg_line(self):
        """Create a plot with 6 graphs by year with avg by year line."""
        fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6)) = plt.subplots(3, 2)
        axes_list = [ax1, ax2, ax3, ax4, ax5, ax6]
        stock_df = self.stock.full_df
        stock_df['year'] = stock_df.date.apply(lambda x: x.strftime('%Y'))
        stock_df['day'] = stock_df.date.apply(lambda x: x.strftime('%j'))
        year_list = stock_df['year'].unique()
        for x in range(len(year_list)):
            year_df = stock_df[stock_df.year == year_list[x]]
            year_avg = year_df.avg.mean()
            axes_list[x].plot(year_df.day, year_df.avg)
            axes_list[x].hlines(y=year_avg, xmin=0, xmax=1)
            axes_list[x].set_title(year_list[x])
        plt.show()

class CompareData:
    """Class to manage comparing of multiple stocks."""

    def __init__(self, stock_list):
        """Initialize instance variables for the comparison data"""
        self.stock_list = stock_list
    
    def five_year_compare(self):
        """Compare each stocks entire 5 year performance."""
        for stock in self.stock_list:
            full_df = stock.full_df


#amd = HistoricalData('amd')
#nvda = HistoricalData('nvda')
#intc = HistoricalData('intc')
khc = HistoricalData('khc')
print(len(khc.full_df))
stock_list = [khc]
yearly = YearlyData(khc)
yearly.yearly_with_avg_line()
yearly.five_year_full()



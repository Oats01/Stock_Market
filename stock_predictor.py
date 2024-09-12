import os
import datetime
import time

import json
from pathlib import Path
import requests
from decouple import config

class SmartStock:
    """The main class of the project."""
    API_KEY = config("api_key")
    def __init__(self):
        """Initialization of the core parameters."""

        self.company = ""
        self.ticker = ""
        self.price_hist = {}
        self.year_avg = []
        self.highs_lows = {}
        self.lows = []
        self.day_avg = []
        self.compared = []
        self.results = []
        self.p = Path('history.json')
        #self.p_3 = Path('history_2.json')
    
    def _get_stock_ticker(self):
        """API call for company ticker."""
        comp_name = input("What Company: ")
        self.company = comp_name.title()
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/auto-complete"
        querystring = {"q":comp_name, "region":"US"}
        headers = {
            "X-RapidAPI-Key": self.API_KEY,
	        "X-RapidAPI-Host": "apidojo-yahoo-finance-v1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        raw_data = response.json()
        lists = raw_data['quotes']
        try:
            self.t_list = lists[0]
        except IndexError:
            print(f"{self.company} is not traded.")
            self._get_stock_ticker()                              

        self.ticker = self.t_list['symbol']
    
    def _get_stock_info(self):
        """API call for the stock information."""
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-chart"
        querystring = {"interval":"1d","symbol":self.ticker,"range":"5y","region":"US","events":"split"}
        headers = {
	        "X-RapidAPI-Key": self.API_KEY,
	        "X-RapidAPI-Host": "apidojo-yahoo-finance-v1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        self.raw_data = response.json()
        #contents = json.dumps(raw_data, indent=4) #Exports json file with indents for readability
        #self.p.write_text(contents) #Only for testing purposes to save file
    
    def _retrieve_stock_info(self):
        """Retrieve info from stored file and save price history"""
        file = self.p.read_text()
        self.raw_data = json.loads(file) #loads a json file to python format
    
    def _create_needed_database(self):
        """Creates a database with required fields from self.raw_data."""
        prices = []
        temp_dict = {}
        chart = self.raw_data['chart']
        result = chart['result']
        info = result[0]
        indicators = info['indicators']
        list = indicators['quote']
        quote = list[0]
        timestamps = info['timestamp']
        open = quote['open']
        high = quote['high']
        low = quote['low']
        close = quote['close']
        volume = quote['volume']
        i=0
        for i in range(len(timestamps)):
            temp_dict['date'] = timestamps[i]
            temp_dict['open'] = open[i]
            temp_dict['high'] = high[i]
            temp_dict['low'] = low[i]
            temp_dict['close'] = close[i]
            temp_dict['volume'] = volume[i]
            prices.append(temp_dict)
            temp_dict = {}
            i += 1
        contents = {}
        contents['prices'] = prices
        
        self.price_hist = contents['prices']
        for dates in self.price_hist:
            form_date = datetime.datetime.fromtimestamp(dates['date'], datetime.UTC).strftime("%m/%d/%Y")
            dates['date'] = form_date

        #data = json.dumps(self.price_hist, indent=4)
        #self.p_3.write_text(data)
    def _split_by_year(self):
        """Splits the main list of dictionarys by year."""
        self.yearly_hist = {}
        temp_list = []
        for x in range(len(self.price_hist)):
            current_data = self.price_hist[x]
            c_day = current_data['date']
            try:
                next_data = self.price_hist[x+1]
                n_day = next_data['date']
            except IndexError:
                temp_list.append(self.price_hist[x])
                marker = c_day[6:]
                self.yearly_hist[marker] = temp_list
            if c_day[6:] == n_day[6:]:
                temp_list.append(self.price_hist[x])
            elif c_day[6:] != n_day[6:]:
                marker = c_day[6:]
                self.yearly_hist[marker] = temp_list
                temp_list = []


    def _calculate_year_average(self):
        """Calculates the yearly average based on highs/lows."""
        self.date_list = []
        for key, year in self.yearly_hist.items():
            highs = []
            lows = []
            highs_lows = []
            for x in range(len(year)):
                dates = year[x]
                try:
                    highs.append(dates['high'])
                    lows.append(dates['low'])
                    self.date_list.append(dates['date'])
                except KeyError:
                    continue
            highs_lows.append(highs)
            highs_lows.append(lows)
            self.highs_lows[key] = highs_lows

        for lists in self.highs_lows.values():
            highs = lists[0]
            lows = lists[1]
            avg = round((sum(highs) + sum(lows))/(len(highs)*2),2)
            self.year_avg.append(avg)

    def _calculate_daily_avg(self):
        """Calculate the daily averge and append to yearly dict."""
        for years in self.yearly_hist.values():
            for day in years:
                high = day['high']
                low = day['low']
                avg = round(((high + low) / 2), 2)
                day['avg'] = avg
    
    def _compare_averages(self):
        """Compares the daily averages against the yearly average."""
        x=0
        for years in self.yearly_hist.values():
            for day in years:
                compared = round((day['avg'] - self.year_avg[x]), 2)
                day['compared'] = compared
            x += 1
    
    def _filter_results(self):
        """Filter the results."""
        self.filtered_dict = {}
        x = 0
        for years, days in self.yearly_hist.items():
            filtered_results = []
            temp_dict = {}
            percent_year = self.year_avg[x] * .02
            i=1
            for day in days:
                if day['compared'] > percent_year and i == len(days):                   
                    temp_dict[day['date']] = day['compared']
                    filtered_results.append(temp_dict)
                    temp_dict = {}
                elif day['compared'] > percent_year:
                    temp_dict[day['date']] = day['compared']
                elif day['compared'] < percent_year and len(temp_dict) > 3:
                    filtered_results.append(temp_dict)
                    temp_dict = {}
                elif day['compared'] < percent_year and len(temp_dict) <= 3:
                    temp_dict = {}
                i += 1
            self.filtered_dict[years] = filtered_results
            x += 1
            
    def _print_results(self):
        """Display the intended results."""
        today = datetime.datetime.today()
        today_str = today.strftime('%m/%d/%Y')
        contents = ""
        i = 0
        x = 0
        for year, days in self.filtered_dict.items(): 
            contents += (f"\n{self.company}:{self.ticker} : {year}: Year Avg: {self.year_avg[i]}\n")
            for day in days:
                dates = []
                results = []
                for key, value in day.items():
                    dates.append(key)
                    results.append(value)
                highs = sorted(results)
                high_value = highs[-1]
                high_day = ""
                for value in results:
                    if high_value == value:
                        high_day = dates[x]
                        x = 0
                        break
                    else:
                        x += 1                
                if dates[-1] != today_str:
                    contents += (f"\n\tTrend Start Date :{dates[0]} with an average price of: {round((results[0]+self.year_avg[i]),2)}")
                    contents += (f"\n\tTrend End Date: {dates[-1]} with an average price of: {round((results[-1]+self.year_avg[i]),2)}")
                    contents += (f"\n\tThe max price was {round((high_value+self.year_avg[i]),2)} on {high_day}\n")
                else:
                    contents += (f"\n\tTrend Start Date :{dates[0]} with an average price of: {round((results[0]+self.year_avg[i]),2)}")
                    contents += (f"\n\tStill trending on {dates[-1]} with an average price of: {round((results[-1]+self.year_avg[i]),2)}")
                    contents += (f"\n\tThe max price was {round((high_value+self.year_avg[i]),2)} on {high_day}\n")
            i += 1
        print(contents)
        user_save = input("\nWould you like to save the query?(yes/no): ")
        if user_save == 'yes':
            self.p_string = f"outputs/{self.company}_{self.ticker}.txt"
            self.p_2 = Path(self.p_string)
            self.p_2.write_text(contents)
    
    def run_program(self):
        """Run all functions of the program."""
        self._get_stock_ticker()
        self._get_stock_info()
        self._create_needed_database()
        self._split_by_year()
        self._calculate_year_average()
        self._calculate_daily_avg()
        self._compare_averages()
        self._filter_results()
        self._print_results()

if __name__ == "__main__":
    st = SmartStock()
    while True:
        st.run_program()
        again = input("Would you like to run another query?(yes/no): ")
        if again == 'yes':
            continue
        else:
            break



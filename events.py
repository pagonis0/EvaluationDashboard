import pandas as pd
import os
import pytz
import time
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from apscheduler.schedulers.background import BackgroundScheduler
from cachetools import TTLCache

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

#comment

class EventHandling:

    def __init__(self):
        self.df = None
        self.cache = TTLCache(maxsize=1, ttl=3600)
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.__fetch, 'interval', minutes=60)
        self.scheduler.start()

    def __fetch(self):
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        print('Fetching new json data... (Creating local cache)')


        try:
            json_data = requests.get('https://success-ai.rz.fh-ingolstadt.de/eventService/get_data_from_db',
                                     verify=False).json()
            self.cache['data'] = json_data
            self.df = pd.DataFrame(json_data['data'])

        except requests.exceptions.RequestException as e:
            print(f"Could not access Event Collection Data (EVC): {e}")
            if 'data' in self.cache:
                cached_data = self.cache['data']
                self.df = pd.DataFrame(cached_data)
                print("Using cached data.")
            else:
                print("Error loading cached data. No cached data available.")
                self.df = pd.DataFrame()

        return self.df

    def preprocess(self):
        if self.__fetch() is None:
            return None

        usr_rmv = [-20, -10, -1, 2, 3, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                   99, 101, 103, 117, 119, 120, 122, 123, 131, 145, 146, 149, 156, 161, 248]
        crs_rmv = [1, 2, 3, 5, 6, 10, 13, 14, 15, 16, 17, 23, 24, 26, 28, 33]

        self.df['user_id'] = self.df['user_id'].astype(int)
        self.df['courseid'] = self.df['courseid'].astype(int)

        # Filter out rows
        self.df = self.df[~self.df['user_id'].isin(usr_rmv)]
        self.df = self.df[~self.df['courseid'].isin(crs_rmv)]

        self.df['timecreated'] = pd.to_datetime(self.df['timecreated'])

        self.df['timecreated'] = pd.to_datetime(self.df['timecreated'], unit='s')
        self.df['month'] = self.df['timecreated'].dt.strftime("%Y-%m")
        self.df['week'] = self.df['timecreated'].dt.isocalendar().week
        self.df['year-week'] = self.df['timecreated'].dt.strftime("%G-%V")
        self.df['year'] = self.df['timecreated'].dt.year
        self.df['day'] = self.df['timecreated'].dt.date

        return self.df

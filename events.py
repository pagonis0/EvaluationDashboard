import pandas as pd
import os
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import time
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)


class EventHandling:

    def __init__(self):
        self.df = None
        self.cache_file = 'event_data_cache.json'
        self.scheduler = BackgroundScheduler()

        # Schedule the update_data function to run every night at 01:00 GMT+2
        self.scheduler.add_job(self.__update_data, 'cron', hour=1, minute=0, timezone=pytz.timezone('Europe/Berlin'))
        self.scheduler.start()

    def __update_data(self):
        # Function to update data and cache
        print('Updating data and cache...')
        self.__fetch()

    def __fetch(self):
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

        print('Fetching new json data... (Creating local cache)')

        try:
            json_data = requests.get('https://success-ai.rz.fh-ingolstadt.de/eventService/get_data_from_db',
                                     verify=False).json()
            self.df = pd.DataFrame(json_data['data'])

            # Save the latest data to cache
            with open(self.cache_file, 'w') as cache_file:
                json.dump(json_data, cache_file)

        except requests.exceptions.RequestException as e:
            print(f"Could not access Event Collection Data (EVC): {e}")

            # Try to load data from cache
            if os.path.exists(self.cache_file):
                try:
                    with open(self.cache_file, 'r') as cache_file:
                        cached_data = json.load(cache_file)
                        self.df = pd.DataFrame(cached_data['data'])
                        print("Using cached data.")
                        return self.df
                except Exception as cache_exception:
                    print(f"Error loading cached data: {cache_exception}")
                    return pd.DataFrame()  # Return an empty DataFrame

        return self.df

    def preprocess(self):
        if self.__fetch() is None:
            return None

        usr_rmv = [-20, -10, -1, 2, 3, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                   99, 101, 103, 117, 119, 120, 122, 123, 131, 145, 146, 149, 156, 161, 248]
        mask = self.df['user_id'].isin(usr_rmv)
        self.df = self.df[~mask]
        self.df['timecreated'] = pd.to_datetime(self.df['timecreated'])

        self.df['timecreated'] = pd.to_datetime(self.df['timecreated'], unit='s')
        self.df['month'] = self.df['timecreated'].dt.strftime("%Y-%m")
        self.df['week'] = self.df['timecreated'].dt.isocalendar().week
        self.df['year-week'] = self.df['timecreated'].dt.strftime("%G-%V")
        self.df['year'] = self.df['timecreated'].dt.year
        self.df['day'] = self.df['timecreated'].dt.date

        return self.df

import pandas as pd
import os
import time
import json
import requests
import schedule
import threading
from datetime import datetime
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

class EventHandling:
    def __init__(self, event_url: str, metadata_url: str, token: str, meta_fun: str, 
                 cache_file='event_data_cache.json', cache_metadata='metadata_cache.json'):
        self.df = None
        self.metadata = None
        self.cache_file = cache_file
        self.cache_metadata = cache_metadata
        self.event_url = event_url
        self.metadata_url = metadata_url
        self.token = token
        self.meta_fun = meta_fun

    def __fetch(self):
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        if os.path.exists(self.cache_file):
            file_modified_time = os.path.getmtime(self.cache_file)
            current_time = time.time()
            if current_time - file_modified_time < 2 * 3600:
                print('Loading data from cache...', str(datetime.now()))
                with open(self.cache_file, 'r') as file:
                    json_data = json.load(file)
                    self.df = pd.DataFrame(json_data['data'])
                    return self.df
        else:
            print('Cache file not found. Creating a new one.', str(datetime.now()))

        print('Fetching new event data... (Creating local cache)', str(datetime.now()))

        try:
            response = requests.get(self.event_url, verify=False)
            response.raise_for_status()  
            json_data = response.json()
            self.df = pd.DataFrame(json_data['data'])
        except requests.exceptions.RequestException as e:
            print(f"Could not access Event Collection Data (EVC): {e}", str(datetime.now()))
            return None

        with open(self.cache_file, 'w') as file:
            json.dump(json_data, file)

        print('Data loaded!', str(datetime.now()))
        return self.df

    def __get_metadata(self):
        main_link = self.metadata_url
        token = self.token
        func = self.meta_fun
        url = f"{main_link}?wstoken={token}&wsfunction={func}&moodlewsrestformat=json"

        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        if os.path.exists(self.cache_metadata):
            file_modified_time = os.path.getmtime(self.cache_metadata)
            current_time = time.time()
            if current_time - file_modified_time < 2 * 3600:
                print('Loading metadata from cache...', str(datetime.now()))
                with open(self.cache_metadata, 'r') as file:
                    json_data = json.load(file)
                    dfs = []
                    for data in json_data:
                        df_meta = pd.json_normalize(data['meta_data_info'])
                        df_module = pd.json_normalize(data['module_base_info']).drop(['id', 'visible', 'name'], axis=1)
                        df_section = pd.json_normalize(data['section_base_info']).drop(['resp_id'], axis=1)
                        lns = pd.concat([df_meta, df_module, df_section], axis=1)
                        dfs.append(lns)

                    self.metadata = pd.concat(dfs, ignore_index=True)
                    return self.metadata
        else:
            print('Cache file not found. Creating a new one.', str(datetime.now()))

        print('Fetching new Metadata data... (Creating local cache)', str(datetime.now()))

        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()  
            json_data = response.json()

            dfs = []
            for data in json_data:
                df_meta = pd.json_normalize(data['meta_data_info']).drop(['id'], axis=1)
                df_module = pd.json_normalize(data['module_base_info']).drop(['id', 'visible', 'name'], axis=1)
                df_section = pd.json_normalize(data['section_base_info']).drop(['resp_id'], axis=1)
                lns = pd.concat([df_meta, df_module, df_section], axis=1)
                dfs.append(lns)

            self.metadata = pd.concat(dfs, ignore_index=True)
        except requests.exceptions.RequestException as e:
            print(f"Could not access Metadata: {e}", str(datetime.now()))
            return None

        with open(self.cache_metadata, 'w') as file:
            json.dump(json_data, file)

        print('Data loaded!', str(datetime.now()))
        return self.metadata

    def preprocess(self):
        if self.__fetch() is None:
            return None

        if self.__get_metadata() is None:
            return None

        usr_rmv = [-20, -10, -1, 2, 3, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 99, 101, 103, 117, 119, 120, 122, 123, 131, 145, 146, 149, 156, 161, 248]
        crs_rmv = [1, 2, 3, 5, 6, 10, 13, 14, 15, 16, 17, 23, 24, 26, 28, 33]

        self.df['user_id'] = self.df['user_id'].astype(int)
        self.df['courseid'] = self.df['courseid'].astype(int)
        self.df = self.df.dropna(subset=['objectid'])
        self.df['objectid'] = self.df['objectid'].astype(int)
        self.metadata['course'] = self.metadata['course'].astype(int)

        self.df = self.df[~self.df['user_id'].isin(usr_rmv)]
        self.df = self.df[~self.df['courseid'].isin(crs_rmv)]
        self.metadata = self.metadata[~self.metadata['course'].isin(crs_rmv)]

        self.df['timecreated'] = pd.to_datetime(self.df['timecreated'], unit='s')
        self.df['month'] = self.df['timecreated'].dt.strftime("%Y-%m")
        self.df['week'] = self.df['timecreated'].dt.isocalendar().week
        self.df['year-week'] = self.df['timecreated'].dt.strftime("%G-%V")
        self.df['year'] = self.df['timecreated'].dt.year
        self.df['day'] = self.df['timecreated'].dt.date

        self.df['semester'] = 'Winter Semester'
        self.df.loc[self.df['timecreated'].dt.month.between(3, 9), 'semester'] = 'Sommer Semester'

        self.df = self.df.merge(self.metadata, how='left', left_on='nuggetName', right_on='content_name')
        self.df = self.df[self.df['is_ln'] == 1]
        self.df = self.df[~self.df['content_name'].isin(['Python Zusammenfassung', 'Python summary (english)'])]

        DIFFICULTY_MAP = {
            "0": "None",
            "1": "Nicht zutreffend",
            "2": "Einfach",
            "3": "Fortgeschritten",
            "4": "Schwer"
        }

        self.df["difficulty"] = self.df["difficulty"].map(DIFFICULTY_MAP)

        print('Data combined and ready to use!', str(datetime.now()))
        return self.df

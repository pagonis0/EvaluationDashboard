import pandas as pd
from pandas import json_normalize
from datetime import date, time
from tqdm import tqdm
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from matplotlib.colors import Normalize
import seaborn as sns
import pickle


requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

class GradeHandling:

    def __init__(self):
        self.df = None
        self.cache_filename = 'grade_cache.pkl'

    def _fetch(self):

        try:
            with open(self.cache_filename, 'rb') as cache_file:
                all_entries = pickle.load(cache_file)
                print("Loaded data from local cache.")
        except FileNotFoundError:
            all_entries = []

        url = "https://success.thi.de/webservice/rest/server.php"
        token = "38cb1aa68d55c4f2d8dcb691a306b2f6"
        function = "local_wstemplate_get_all_grades"
        format = "json"
        max_limit = 3000000000

        offset = 0
        limit = 2000


        while True:
            data = []
            params = {
                'wstoken': token,
                'wsfunction': function,
                'moodlewsrestformat': format,
                'limit': limit,
                'offset': offset
            }

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"Error: {response.status_code}")
                break

            data = response.json()

            # Check if data is empty or reaches the end
            if not data:
                print("Reached end of data.")
                break

            # Process the data as needed
            all_entries.extend(data)

            # Update offset for the next request
            offset += limit

            # Break if offset exceeds the maximum limit
            if offset >= max_limit:
                print("Reached maximum limit.")
                break

        if all_entries:
            result_json = json.dumps(all_entries)
            parsed_data = json.loads(result_json)

            with open(self.cache_filename, 'ab') as cache_file:
                pickle.dump(data, cache_file)

        return all_entries

    def preprocess(self):
        try:
            with open(self.cache_filename, 'rb') as cache_file:
                self.df = pd.DataFrame(pickle.load(cache_file))
                print("Loaded data from local cache.")
        except FileNotFoundError:
            print("Cache file not found. Fetching data from API.")
            self.df = self._fetch()

        if self.df is None:
            return None

        self.df = pd.concat([
            pd.json_normalize(self.df['course_info']),
            pd.json_normalize(self.df['module_base_info']).drop(['id', 'visible', 'resp_id'], axis=1),
            pd.json_normalize(self.df['grade_base_info']),
            pd.json_normalize(self.df['meta_data_info']).drop(['customfield_id', 'customfield_data_id'], axis=1)
        ], axis=1)

        self.df['grade'] = 100 * (self.df['rawgrademax'] - self.df['rawgrade']) / self.df['rawgrademax']


        usr_rmv = [-20, -10, -1, 2, 3, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                   99, 101, 103, 117, 119, 120, 122, 123, 131, 145, 146, 149, 156, 161, 248]
        mask = self.df['userid'].isin(usr_rmv)
        self.df = self.df[~mask]
        self.df = self.df.dropna(subset=['grade', 'timemodified'])
        self.df = self.df.reset_index(drop=True)

        self.df['timecreated'] = pd.to_datetime(self.df['timemodified'])

        self.df['timemodified'] = pd.to_datetime(self.df['timemodified'], unit='s')
        self.df['month'] = self.df['timemodified'].dt.strftime("%Y-%m")
        self.df['week'] = self.df['timemodified'].dt.isocalendar().week
        self.df['year-week'] = self.df['timemodified'].dt.strftime("%G-%V")
        self.df['year'] = self.df['timemodified'].dt.year
        self.df['day'] = self.df['timemodified'].dt.date

        return self.df

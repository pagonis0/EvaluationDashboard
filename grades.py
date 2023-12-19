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

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

class GradeHandling:

    def __init__(self):
        self.df = None

    def _fetch(self):
        url = "https://success.thi.de/webservice/rest/server.php"
        token = "38cb1aa68d55c4f2d8dcb691a306b2f6"
        function = "local_wstemplate_get_all_grades"
        format = "json"
        max_limit = 3000000000

        offset = 0
        limit = 2000

        all_entries = []

        while True:
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

        result_json = json.dumps(all_entries)
        parsed_data = json.loads(result_json)

        #self.df = pd.DataFrame(parsed_data['module_base_info'])
        #print(self.df)

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

grades = GradeHandling()
print(grades._fetch())
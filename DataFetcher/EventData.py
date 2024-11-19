import pandas as pd
import os, time, json, requests
from datetime import datetime
import numpy as np
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.simplefilter('ignore', InsecureRequestWarning)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pd.set_option('mode.chained_assignment', None)

#TODO: Add documentation to classes and methods

class EventHandling:
    """
    The EventHandling class manages data retrieval and preprocessing for the Event Collection Database (ECD).
    It caches data locally to reduce the frequency of API requests and performs basic data preprocessing 
    to prepare the data for graphical representation, particularly within Moodle instances.

    This class is intended to retrieve and process event and metadata related to 'Learning Nuggets', 
    which are instructional units within Moodle. It handles fetching and caching of data, filtering 
    irrelevant data, and performing transformations necessary for subsequent visualization.

    Attributes:
    cache_file (str): The filename where the event data cache is stored.
    cache_metadata (str): The filename where the metadata cache is stored.

    Author:
    Panos Pagonis, panos.pagonis@thi.de
    The main methods are:
    __init__()
    __fetch()
    preprocess()
    """
    def __init__(self, cache_file='event_data_cache.json', cache_metadata = 'metadata_cache.json'):
        """
        Initializes the EventHandling object. Optionally accepts custom filenames for caching event data
        and metadata. If no cache files are present, new data will be fetched from the appropriate sources.

        :parameters:
        cache_file (str): Path to the JSON file where event data will be cached. Default is 'event_data_cache.json'.
        cache_metadata (str): Path to the JSON file where metadata will be cached. Default is 'metadata_cache.json'.

        :return: None
        """
        self.df = None
        self.metadata = None
        self.cache_file = cache_file
        self.cache_metadata = cache_metadata


    def __fetch(self):
        """
        Method to call the data from the ECD. It strores the data in a DataFrame object.
        If the data exists already calls them from a file, but if they are expired
        (file older than 2h) call a new set of data.
        :return: pandas.DataFrame object with all the data from ECD
        """
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
            json_data = requests.get('https://success-ai.rz.fh-ingolstadt.de/eventService/get_data_from_db',
                                     verify=False).json()
            self.df = pd.DataFrame(json_data['data'])
        except requests.exceptions.RequestException as e:
            print(f"Could not access Event Collection Data (EVC): {e}", str(datetime.now()))

        with open(self.cache_file, 'w') as file:
            json.dump(json_data, file)
        
        print('Data loaded!', str(datetime.now()))


        return self.df
    
    def __get_metadata(self):
        main_link = "https://success.thi.de/webservice/rest/server.php"
        token = "38cb1aa68d55c4f2d8dcb691a306b2f6"
        func = "local_wstemplate_get_all_learning_nuggets_new"
        base_url = f"{main_link}?wstoken={token}&wsfunction={func}&moodlewsrestformat=json&course_id="

        # Check if cache is up-to-date
        if os.path.exists(self.cache_metadata):
            file_modified_time = os.path.getmtime(self.cache_metadata)
            current_time = time.time()
            if current_time - file_modified_time < 2 * 3600:
                print('Loading metadata from cache...', str(datetime.now()))
                with open(self.cache_metadata, 'r') as file:
                    json_data = json.load(file)
                    return self._aggregate_metadata(json_data)

        # Fetch new metadata if cache is missing or expired
        print('Cache file not found or outdated. Fetching new metadata data...', str(datetime.now()))

        course_ids = self.df['courseid'].unique()  # Collect unique course IDs from the fetched event data
        all_metadata = []

        for course_id in course_ids:
            url = base_url + str(course_id)
            try:
                response = requests.get(url, verify=False).json()
                print(f"Accessing metadata for course ID {course_id}", str(datetime.now()))
                if isinstance(response, dict) and 'exception' in response:
                    print(f"Error fetching data for course ID {course_id}: {response['message']}")
                    continue  # Skip this courseid if it returned an error
                all_metadata.append(response)
                time.sleep(0.2) 
            except Exception as e:
                print(f"Could not access Metadata for course ID {course_id}: {str(e)}", str(datetime.now()))

        all_metadata = [entry for entry in all_metadata if entry]
        if all_metadata:
            with open(self.cache_metadata, 'w') as file:
                json.dump(all_metadata, file)
                print("Metadata cached successfully!")
        else:
            print("No valid metadata to cache.")

        return self._aggregate_metadata(all_metadata)

    def _aggregate_metadata(self, metadata_json):
        """
        Aggregates metadata JSON into a DataFrame for analysis. 

        :parameters:
        metadata_json (list): List of metadata JSON responses for each course

        :return: pandas.DataFrame with aggregated metadata
        """
        dfs = []
        for data_list in metadata_json:
            for data in data_list:
                df_meta = pd.json_normalize(data['meta_data_info']).drop(['id'], axis=1, errors='ignore')
                df_module = pd.json_normalize(data['module_base_info']).drop(['id', 'visible', 'name'], axis=1, errors='ignore')
                df_section = pd.json_normalize(data['section_base_info']).drop(['resp_id'], axis=1, errors='ignore')
                lns = pd.concat([df_meta, df_module, df_section], axis=1)
                dfs.append(lns)
        if dfs:            
            result_df = pd.concat(dfs, ignore_index=True)
            return result_df
        else:
            print("No valid metadata entries found.")
            return pd.DataFrame()  

    def preprocess(self):
        """
        The method performs a basic preprocessing of the dataset.
        It transforms the times to pandas.datetime and generates
        week, day and year.
        Additionally it combines event data with the metadata, cleans
        and prepares the dataset for the graphical visualitation.
        :return: pandas.DataFrame object with the newly added columns
        """
        self.df = self.__fetch()
        self.metadata = self.__get_metadata()

        if self.df is None or self.df.empty:
            print("No event data available for preprocessing.")
            return None
        
        if self.metadata is None or self.metadata.empty:
            print("No metadata available for preprocessing.")
            return None

        # In the current stutus non-students users and test courses should be manually removed
        # With the newest event collection db the user role should be included
        usr_rmv = [-20, -10, -1, 2,3,5,6,7,9,11,12,13,14,15,16,17,18,19,20,
                   37,54,60,99,116,117,119,120,122,123,124,131,145,146,156,
                   161,183,184,185,187,188,189,191,192,193,194,199,366,382,
                   386,391,396,397,403,404,405,406,407,408,411,412,434,439,
                   443,446,447,449,491,492,506,511,540,552,557,560]
        crs_rmv = [1, 2, 3, 5, 6, 10, 13, 14, 15, 16, 17, 24, 26, 28, 33]

        self.df['user_id'] = self.df['user_id'].astype(int)
        self.df['courseid'] = self.df['courseid'].astype(int)
        self.df = self.df.dropna(subset=['objectid'])
        self.df['objectid'] = self.df['objectid'].astype(int)
        self.metadata['course'] = self.metadata['course'].astype(int)

        # Filter out rows
        self.df = self.df[~self.df['user_id'].isin(usr_rmv)]
        self.df = self.df[~self.df['courseid'].isin(crs_rmv)]
        self.metadata = self.metadata[~self.metadata['course'].isin(crs_rmv)]

        self.df['timecreated'] = pd.to_datetime(self.df['timecreated'])

        self.df['timecreated'] = pd.to_datetime(self.df['timecreated'], unit='s')
        self.df['month'] = self.df['timecreated'].dt.strftime("%Y-%m")
        self.df['week'] = self.df['timecreated'].dt.isocalendar().week
        self.df['year-week'] = self.df['timecreated'].dt.strftime("%G-%V")
        self.df['year'] = self.df['timecreated'].dt.year
        self.df['day'] = self.df['timecreated'].dt.date

        self.df['semester'] = 'Winter Semester'
        self.df.loc[self.df['timecreated'].dt.month.between(3, 9), 'semester'] = 'Sommer Semester'

        self.df = self.df.merge(self.metadata, how='left', left_on='nuggetName', right_on='content_name')
        self.df = self.df[self.df['is_ln']==1]
        self.df = self.df[self.df['content_name'] != 'Python Zusammenfassung']
        self.df = self.df[self.df['content_name'] != 'Python summary (english)']

        DIFFICULTY_MAP = {
            "0": "None",
            "1": "Nicht zutreffend",
            "2": "Einfach",
            "3": "Fortgeschritten",
            "4": "Schwer"
        }

        self.df["difficulty"] = self.df["difficulty"].map(DIFFICULTY_MAP)

        conditions = [
            self.df['example'] == 1,
            self.df['motivation'] == 1,
            self.df['explanation'] == 1,
            self.df['assignment'] == 1,
            self.df['experiment'] == 1
        ]
        choices = ['Beispiel', 'Motivation', 'Erklärung', 'Aufgabe', 'Anwendung']

        self.df['type'] = np.select(conditions, choices, default='')

        self.df = self.df.drop(['anonymous', 'component', 'contextid', 'contextinstanceid', 'contextlevel', 'crud', 'edulevel', 'eventname', 'lectureDate',
                'others', 'quizid', 'recourceFiletype', 'relateduserid', 'scromId', 'scromNeeded', 'target', 'id', 'course', 'module', 'instance',
                'resp_id', 'example', 'motivation', 'motivation', 'assignment', 'experiment', 'sectionnumber', 'content_name'], axis=1, errors='ignore')
        
        print('Data combined and ready to use!', str(datetime.now()))
        print(self.df.columns)
        return self.df

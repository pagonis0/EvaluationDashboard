import pandas as pd
import os, time, json, requests
from datetime import datetime
import numpy as np
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings

warnings.simplefilter('ignore', InsecureRequestWarning)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

class ChatbotDataHadling:
    """
    The ChatbotDataHadling class manages data retrieval and preprocessing for the Chatbot Database.
    It caches data locally to reduce the frequency of API requests and performs basic data preprocessing 
    to prepare the data for graphical representation.

    This class is intended to retrieve and process the chatbot discussions.
    It handles fetching and caching of data, filtering irrelevant data, 
    and performing transformations necessary for subsequent visualization.

    Attributes:
    cache_file (str): The filename where the event data cache is stored.

    Author:
    Panos Pagonis, panos.pagonis@thi.de
    The main methods are:
    __init__()
    __fetch()
    preprocess()
    """

    def __init__(self, cache_file='chat_history.json'):
        self.df = None
        self.cache_file = cache_file

    
    def __fetch(self):
        """
        Method to call the data from the ChatBot DB. It strores the data in a DataFrame object.
        If the data exists already calls them from a file, but if they are expired
        (file older than 2h) call a new set of data.
        :return: pandas.DataFrame object with all the data from DB
        """
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        if os.path.exists(self.cache_file):
            file_modified_time = os.path.getmtime(self.cache_file)
            current_time = time.time()
            if current_time - file_modified_time < 3600:
                print('Loading chat hostory from cache...', str(datetime.now()))
                with open(self.cache_file, 'r') as file:
                    json_data = json.load(file)
                    messages_list = json_data['messages']
                    flattened_messages = [message for sublist in messages_list for message in sublist]
                    self.df = pd.DataFrame(flattened_messages)
                    return self.df
        else:
            print('Cache file not found. Creating a new one.', str(datetime.now()))

        print('Fetching the newest chat histories... (Creating local cache)', str(datetime.now()))


        try:
            json_data = requests.post('http://10.10.240.28:13391/api/request-data-for-analytics',
                                     verify=False).json()
            self.df = pd.DataFrame(json_data['messages'])
        except requests.exceptions.RequestException as e:
            print(f"Could not access ChatBot API: {e}", str(datetime.now()))

        with open(self.cache_file, 'w') as file:
            json.dump(json_data, file)
        
        print('Data loaded!', str(datetime.now()))


        return self.df
    

    def preprocess(self):
        """
        The method performs a basic preprocessing of the dataset.
        It transforms the times to pandas.datetime.
        :return: pandas.DataFrame object with the newly added columns
        """
        if self.__fetch() is None:
            return None
        self.df['user_id'] = self.df['user_id'].astype(int)
        self.df['datetime'] = pd.to_datetime(self.df['datetime'])
        self.df['generation_info'] = self.df['generation_info'].apply(lambda x: x['generation_time'] if x else None)

        return self.df

from EventData import EventHandling
from ChatbotData import ChatbotDataHadling
from datetime import datetime
import os
import pandas as pd

"""
CRON Job Script for Event Data Processing
==========================================
This script is intended to be used in a scheduled CRON job for automating event data processing tasks.
It uses the `EventHandling` class from the `events` module to handle data preprocessing, and saves the processed data to a CSV file.
"""

print("CRON Job started", str(datetime.now()))

current_working_directory = os.getcwd()
print(f"Current working directory: {current_working_directory}", str(datetime.now()))

event_file_path = '/app/dataset.csv'
chatbot_file_path = '/app/messages.csv'

try:
    event_handler = EventHandling()
    df = event_handler.preprocess()

    if os.path.exists(event_file_path):
        os.remove(event_file_path)
        print(f"Existing file {event_file_path} removed", str(datetime.now()))
    else:
        print(f"{event_file_path} does not exist, creating new file", str(datetime.now()))

    df.to_csv(event_file_path, index=False)
    print(f"Dataset saved to {event_file_path}", str(datetime.now()))

except Exception as e:
    print(f"An error occurred: {e}", str(datetime.now()))

try:
    chatbot_data = ChatbotDataHadling()
    df = chatbot_data.preprocess()

    if os.path.exists(chatbot_file_path):
        os.remove(chatbot_file_path)
        print(f"Existing file {chatbot_file_path} removed", str(datetime.now()))
    else:
        print(f"{chatbot_file_path} does not exist, creating new file", str(datetime.now()))

    df.to_csv(chatbot_file_path, index=False)
    print(f"Chatbot messages saved to {chatbot_file_path}", str(datetime.now()))

except Exception as e:
    print(f"An error occurred to chatbot data: {e}", str(datetime.now()))

print("CRON Job ready", str(datetime.now()))

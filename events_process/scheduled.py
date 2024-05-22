from events import EventHandling
from datetime import datetime
import os

print("CRON Job started", str(datetime.now()))

current_working_directory = os.getcwd()
print(f"Current working directory: {current_working_directory}")

try:
    event_handler = EventHandling()
    df = event_handler.preprocess()

    # Use an absolute path to save the dataset
    output_file = '/Users/pagonis/Documents/THI/THISuccess/Code/TestEval/dataset.csv'
    df.to_csv(output_file, index=False)

    print(f"Dataset saved to {output_file}", str(datetime.now()))
except Exception as e:
    print(f"An error occurred: {e}", str(datetime.now()))

print("CRON Job ready", str(datetime.now()))
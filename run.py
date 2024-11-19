import logging
from FlaskDash import app
import threading
import time
from dataset import import_dataset

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


# Load data initially
def load_data():
    with app.config['data_lock']:
        app.config['data'] = import_dataset()
        logging.info("Dataset loaded successfully.")

def refresh_data():
    while True:
        time.sleep(180)  # Refresh every 3 minutes
        load_data()
        logging.info("Dataset refreshed.")

# Initialize data and start the refresh thread
with app.app_context():
    app.config['data'] = None
    app.config['data_lock'] = threading.Lock()
    load_data()
    data_refresh_thread = threading.Thread(target=refresh_data)
    data_refresh_thread.daemon = True
    data_refresh_thread.start()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7005)

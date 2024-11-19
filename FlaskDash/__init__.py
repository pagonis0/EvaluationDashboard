from flask import Flask, session, abort, request
from flask_session import Session
from UsageDashboard import create_usage_board
from ChatbotDashboard import create_chatbot_board
import threading, json, time, random, os
from dataset import import_dataset
import psutil

from RecommendationSystem.api import MoodleAPI, RecommenderAPI
from RecommendationSystem.dash_layout import init_dash, dash_layout, dynamic_layout, difference


def init_app():

    f_app = Flask(__name__, static_url_path='/flaskdash/static')
    f_app.config['SECRET_KEY'] = '061f21bcd3a44531574c97c17b75da45'
    f_app.config.from_file("/app/config.json", load=json.load)
    Session(f_app)
    d_app = init_dash(f_app, session)
    from FlaskDash.main.routes import main
    from FlaskDash.dash.routes import dash
    from FlaskDash.interface.routes import interface
    f_app.register_blueprint(main)
    f_app.register_blueprint(dash)
    f_app.register_blueprint(interface)

    return f_app, d_app


app, dash = init_app()

create_usage_board(app)
create_chatbot_board(app)
#create_score_board(app)


# ============ init ============
with app.app_context():
    moodle = MoodleAPI()
    recommender = RecommenderAPI()
    lns_json, lns_table, cmid2lnid, course_table = moodle._get_lns()
    random.seed(a=42)

print(">>> loaded:", psutil.Process(os.getpid()).memory_info().rss / 1024)

@app.context_processor
def inject_interface_flag():
    return {'is_interface': '/interface' in request.path}

data = None
data_lock = threading.Lock()

def load_data():
    global data
    with data_lock:
        data = import_dataset()

def refresh_data():
    while True:
        time.sleep(1800) 
        load_data()

@app.context_processor
def inject_interface_flag():
    return {'is_interface': '/interface' in request.path}

@app.context_processor
def inject_dash_flag():
    return {'is_dash': '/dash' in request.path}

load_data()

# Start the background data refresh thread
data_refresh_thread = threading.Thread(target=refresh_data)
data_refresh_thread.daemon = True
data_refresh_thread.start()

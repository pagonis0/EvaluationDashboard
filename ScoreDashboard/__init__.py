import dash
from dash import html, dcc, Output, Input, dash_table
import dash_daq as daq
import plotly.express as px
from events_process.events import EventHandling
import pandas as pd
import dash_bootstrap_components as dbc
from datetime import datetime

event_handler = EventHandling()
df = event_handler.preprocess()


def create_score_board(flask_app):
    dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname="/dash/graphs/score/", meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                         external_stylesheets=[dbc.themes.BOOTSTRAP, "/static/styles.css"])
    
    # TODO: When grades are avaliable
       
    return dash_app

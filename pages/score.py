import dash
from dash import Dash, html, dcc, callback, Output, Input, ClientsideFunction
import dash_daq as daq
import plotly.express as px
from datetime import datetime as dt

dash.register_page(__name__)




def score_filters():
    """

    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            #Select year
            html.P("Studienjahr auswählen"),
            dcc.Dropdown(
                id="academic-year",
                options=[
                    {'label': '2022/2023', 'value': '2022/2023'},
                    {'label': '2023/2024', 'value': '2024/2024'},
                ],
                value='2022/2023',
            ),
            html.Br(),
            #Select course
            html.P("Kurs auswählen"),
            dcc.Dropdown(
                id="couse",
                options=[
                    {'label': 'Mathe 1', 'value': 'Mathe 1'},
                    {'label': 'Statistik 1', 'value': 'Statistik 1'},
                    {'label': 'Elektrotechnik 1', 'value': 'Elektrotechnik 1'},
                ],
                value='Mathe 1',
            ),
            html.Br(),
            #Select Topic
            html.P("Learning Block auswählen"),
            dcc.Dropdown(
                id="LB-select",
                options=[
                    {'label': 'Matrices', 'value': 'Matrices'},
                    {'label': 'Eigenwerte', 'value': 'Eigenwerte'},
                    {'label': 'Alle', 'value': 'Alle'},
                ],
                value='Alle',
                multi=False,
            ),
            html.Br(),
            #Select Specific LN
            html.P("Learning Nugget auswählen"),
            dcc.Dropdown(
                id="LN-select",
                options=[
                    {'label': 'Learning Nugget ABC', 'value': 'abc'},
                    {'label': 'Learning Nugget DEF', 'value': 'def'},
                    {'label': 'Learning Nugget XYZ', 'value': 'xyz'},
                ],
                multi=True,
            ),
            html.Br(),
            #Select Difficulty
            html.P("Learning Nugget schwierigkeit"),
            dcc.Dropdown(
                id="admit-select",
                options=[
                           {'label': 'Kein Schwierigkeit', 'value': 'San Francisco'},
                           {'label': 'Einfach', 'value': 'New York City'},
                           {'label': 'Medium', 'value': 'Montreal'},
                           {'label': 'Schwer', 'value': 'San Francisco'},
                       ],
                value='Medium',
                multi=True,
            ),
            html.Br(),
            # Only recommended LNs
            html.P("Emphohlene Learning Nuggets anzeigen"),
            daq.ToggleSwitch(
                id='rec-LN',
                value=False,
                theme='dark',
                color='blue'
            ),
            html.Br(),
            # Select time of the day
            html.P("Uhrzeit auswählen"),
            dcc.Dropdown(
                id="timezone-select",
                options=[
                    {'label': 'Vormittags', 'value': 'abc'},
                    {'label': 'Nachmittags', 'value': 'def'},
                    {'label': 'Abends', 'value': 'xyz'},
                    {'label': 'Nachts', 'value': 'xyz'}
                ],
                multi=True,
            ),
            html.Br(),
            # Select day range
            html.P("Datum auswählen"),
            dcc.DatePickerRange(
                id="date-picker-select",
                start_date=dt(2022, 10, 1),
                end_date=dt(2023, 9, 30),
                min_date_allowed=dt(2022, 10, 1),
                max_date_allowed=dt(2023, 9, 30),
                initial_visible_month=dt(2022, 10, 1),
            ),
            html.Br(),
            html.Div(
                id="reset-btn-outer",
                children=html.Button(id="reset-btn", children="Reset", n_clicks=0),
            ),
        ],
    )

layout = html.Div(
    id="app-container",
    children=[
        # Left column
        html.Div(
            id="left-column",
            className="four columns",
            children=[score_filters()]
            + [
                html.Div(
                    ["initial child"], id="output-clientside", style={"display": "none"}
                )
            ],
        ),
        # Right column
        html.Div(
            id="right-column",
            className="eight columns",
            children=[
                # Patient Volume Heatmap
                html.Div(
                    id="score_card",
                    children=[
                        html.B("Student Scores"),
                        html.Hr(),
                        dcc.Graph(id="score_graph"),
                    ],
                ),
                # Patient Wait time by Department
                html.Div(
                    id="LNscore_card",
                    children=[
                        html.B("Score per Learning Nugget"),
                        html.Hr(),
                        #html.Div(id="wait_time_table", children=initialize_table()),
                    ],
                ),
            ],
        ),
    ],
)

# Define callback to update the page content based on the URL
@callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])

# Callback to update Patient Volume Heatmap based on button click
@callback(
    Output("patient_volume_hm", "figure"),
    [Input("page-1-button", "n_clicks"), Input("page-2-button", "n_clicks")],
    prevent_initial_call=True
)
def update_patient_volume_graph(page1_clicks, page2_clicks):
    # Replace the following with your actual logic for generating Patient Volume Heatmap
    if page1_clicks > 0:
        # Logic for generating graph for Page 1
        figure = px.scatter(x=[1, 2, 3], y=[10, 11, 12], labels={'x': 'X-axis', 'y': 'Y-axis'})
    elif page2_clicks > 0:
        # Logic for generating graph for Page 2
        figure = px.bar(x=[1, 2, 3], y=[10, 11, 12], labels={'x': 'X-axis', 'y': 'Y-axis'})
    else:
        # Default graph or logic for other pages
        figure = px.line(x=[1, 2, 3], y=[10, 11, 12], labels={'x': 'X-axis', 'y': 'Y-axis'})

    return figure

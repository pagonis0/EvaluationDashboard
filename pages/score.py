"""import dash
from dash import html, dcc, callback, Output, Input, dash_table
import dash_daq as daq
import plotly.express as px
from grades import GradeHandling
import pandas as pd


grade_handler = GradeHandling()

@callback(
    Output('score-hidden-div', 'children'),
    [Input('update-data-btn', 'n_clicks')]
)
def update_score_callback(n_clicks):
    grade_handler.preprocess()
    return None

# Fetch the initial data
df = grade_handler.preprocess()

def extract_academic_years(df):
    years = pd.to_datetime(df['day']).dt.year.unique()
    academic_years = [f"{year}/{year+1}" for year in years]
    return academic_years

dash.register_page(__name__)

def score_filters():
    if grade_handler.df is None:
        print("DataFrame is None. Data fetching may have failed.")
        return html.Div("Error: Data fetching failed.")

    academic_years = extract_academic_years(grade_handler.df)

    return html.Div(
        id="control-card",
        children=[
            #Select year
            html.P("Studienjahr auswählen"),
            dcc.Dropdown(
                id="sc-academic-year",
                options=[],
                value=max(academic_years),
            ),
            html.Br(),
            #Select course
            html.P("Kurs auswählen"),
            dcc.Dropdown(
                id='sc-course-dropdown',
                options=[{'label': course, 'value': course} for course in df['fullname'].unique()],
                multi=True,
                placeholder='Kurs auswählen'
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
                disabled=True,
            ),
            html.Br(),
            #Select Specific LN
            html.P("Learning Nugget auswählen"),
            dcc.Dropdown(
                id='sc-nugget-dropdown',
                multi=True,
                placeholder='Learning Nugget auswählen',
                # style={'whiteSpace': 'nowrap'}
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
                disabled=True,
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
                id='sc-date-picker-range',
                start_date=df['day'].min(),
                end_date=df['day'].max(),
                display_format='YYYY-MM-DD',
                style={'border': 0}
            ),
            html.Br(),
            html.Br(),
            html.Div([
                html.Div(
                    id="sc-reset-btn-outer",
                    children=html.Button(id="sc-reset-btn", children="Reset", n_clicks=0),
                    style={'float': 'right', 'margin-right': '20px'}
                ),
                html.Div(
                    id="update-data-btn-outer",
                    children=html.Button(id="update-data-btn", children="Update Data", n_clicks=0),
                    style={'float': 'right', 'margin-right': '20px'}
                ),
        ],
        className='row'
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
                    children=["initial child"], id="output-clientside1", style={"display": "none"}
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
                        html.B("LN Scores"),
                        html.Hr(),
                        dcc.Graph(id="score-bar-plot"),
                    ],
                ),
                html.Br(),
                html.Div(
                    id="legend-toggle",
                    children=html.Button(id="sc-legend-toggle-btn", children="Toggle Legend", n_clicks=0),
                ),
                # Patient Wait time by Department
                #html.Div(
                #    id="LNscore_card",
                #    children=[
                #        html.B("Score per Learning Nugget"),
                #        html.Hr(),
                #        dash_table.DataTable(id="table")
                        #html.Div(id="wait_time_table", children=initialize_table()),
                #    ],
                #),
            ],
        ),
        html.Div(id='hidden-div', style={'display': 'none'}),
    ],
)

@callback(Output('page-content2', 'children2'),
              [Input('url', 'pathname')])

@callback(
    Output('sc-academic-year', 'options'),
    [Input('update-data-btn', 'n_clicks')])
def update_academic_year_options(n_clicks):
    if grade_handler.df is None:
        return [{'label': 'Error: Data fetching failed', 'value': None}]

    academic_years = extract_academic_years(grade_handler.df)

    options = [{'label': year, 'value': year} for year in academic_years]
    options.insert(0, {'label': 'All', 'value': 'All'})  # Add an option for displaying all data

    return options


@callback(
    Output('sc-nugget-dropdown', 'options'),
    [Input('sc-course-dropdown', 'value')]
)
def update_score_nugget_options(selected_courses):
    if not selected_courses:  # If no course is selected, show all nuggets
        nugget_options = [{'label': nugget, 'value': nugget} for nugget in df['content_name'].unique()]
    else:
        # Filter nuggets based on selected courses
        filtered_df = df[df['fullname'].isin(selected_courses)]
        nugget_options = [{'label': nugget, 'value': nugget} for nugget in filtered_df['content_name'].unique()]

    return nugget_options

# Modify the callback to use the selected_date_range
@callback(
    Output('score-bar-plot', 'figure'),
    [Input('sc-academic-year', 'value'),
     Input('sc-course-dropdown', 'value'),
     Input('sc-nugget-dropdown', 'value'),
     Input('sc-date-picker-range', 'start_date'),
     Input('sc-date-picker-range', 'end_date')]
)
def update_score_bar_plot(academic_year, selected_courses, selected_nuggets, start_date, end_date):
    filtered_df = grade_handler.df.copy()

    if academic_year and academic_year != 'All':
        start_date_range = pd.to_datetime(f'01-10-{academic_year.split("/")[0]}')
        end_date_range = pd.to_datetime(f'30-09-{academic_year.split("/")[1]}') + pd.DateOffset(days=1)
        filtered_df = filtered_df[
            (filtered_df['day'] >= start_date_range.date()) & (filtered_df['day'] < end_date_range.date())
        ]

    if selected_nuggets:
        filtered_df = filtered_df[filtered_df['content_name'].isin(selected_nuggets)]

    if selected_courses:
        filtered_df = filtered_df[filtered_df['fullname'].isin(selected_courses)]

    if start_date and end_date:
        start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
        filtered_df = filtered_df[
            (filtered_df['day'] >= start_date.date()) & (filtered_df['day'] <= end_date.date())
        ]

        # Calculate average daily grade
        avg_daily_grade = filtered_df.groupby('day')['grade'].mean().reset_index()


    # Create bar plot
    fig = px.bar(
        avg_daily_grade,
        x='day',
        y='grade',
        labels={'day': 'Date', 'grade': 'Average Daily Grade'},
        title='Average Daily Grade Over Time'
    )

    return fig



#@callback(Output('score-table', 'data-table'),
#          [Input('sc-nugget-dropdown', 'value'),
#           Input('sc-course-dropdown', 'value'),
#           Input('sc-date-picker-range', 'start_date'),
#           Input('sc-date-picker-range', 'end_date'),
#           Input('sc-legend-toggle-btn', 'n_clicks'),
#           Input("sc-reset-btn", "n_clicks")]
#          )
#def update_data_table(selected_nuggets, selected_courses, start_date, end_date, n_clicks, reset_click):
#    pass"""


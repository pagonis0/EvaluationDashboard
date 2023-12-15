import dash
from dash import Dash, html, dcc, callback, Output, Input, ClientsideFunction
import dash_daq as daq
import plotly.express as px
from dash import clientside_callback
import plotly.graph_objects as go
from datetime import datetime as dt
from events import EventHandling
import pandas as pd


event_handler = EventHandling()
df = event_handler.preprocess()


dash.register_page(__name__)

def usage_filters():
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
                id='course-dropdown',
                options=[{'label': course, 'value': course} for course in df['coursename'].unique()],
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
            ),
            html.Br(),
            #Select Specific LN
            html.P("Learning Nugget auswählen"),
            dcc.Dropdown(
                id='nugget-dropdown',
                multi=True,
                placeholder='Learning Nugget auswählen',
                #style={'whiteSpace': 'nowrap'}
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
            # Select day range
            html.P("Datum auswählen"),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=df['day'].min(),
                end_date=df['day'].max(),
                display_format='YYYY-MM-DD'
            ),
            html.Br(),
            html.Br(),
            html.Div(
                id="reset-btn-outer",
                children=html.Button(id="reset-btn", children="Reset", n_clicks=0),
            ),
            #html.Div(
            #    id="legend-toggle",
            #    children=html.Button(id="legend-toggle-btn", children="Toggle Legend", n_clicks=0),
            #),
        ],
    )

layout = html.Div(
    id="app-container",
    children=[
        # Left column
        html.Div(
            id="left-column",
            className="four columns",
            children=[usage_filters()]
            + [
                html.Div(
                    ["initial child"], id="output-clientside1", style={"display": "none"}
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
                    id="usage_card",
                    children=[
                        html.B("LN Usage"),
                        html.Hr(),
                        dcc.Graph(id="bar-plot"),
                    ],
                ),
                html.Div(
                    id="legend-toggle",
                    children=html.Button(id="legend-toggle-btn", children="Toggle Legend", n_clicks=0),
            ),
                # Patient Wait time by Department
                html.Div(
                    id="LNusage_card",
                    children=[
                        html.B("Zsage per Learning Nugget"),
                        html.Hr(),
                        #html.Div(id="wait_time_table", children=initialize_table()),
                    ],
                ),
            ],
        ),
        html.Div(id='hidden-div', style={'display': 'none'}),
    ],
)


# Define callback to update the page content based on the URL
@callback(Output('page-content1', 'children1'),
              [Input('url', 'pathname')])

@callback(
    Output('nugget-dropdown', 'options'),
    [Input('course-dropdown', 'value')]
)
def update_nugget_options(selected_courses):
    if not selected_courses:  # If no course is selected, show all nuggets
        nugget_options = [{'label': nugget, 'value': nugget} for nugget in df['nuggetName'].unique()]
    else:
        # Filter nuggets based on selected courses
        filtered_df = df[df['coursename'].isin(selected_courses)]
        nugget_options = [{'label': nugget, 'value': nugget} for nugget in filtered_df['nuggetName'].unique()]

    return nugget_options

# Modify the callback to use the selected_date_range
@callback(
    Output('bar-plot', 'figure'),
    [Input('nugget-dropdown', 'value'),
     Input('course-dropdown', 'value'),
     Input('date-picker-range', 'start_date'),
     Input('date-picker-range', 'end_date'),
     Input('legend-toggle-btn', 'n_clicks'),
     Input("reset-btn", "n_clicks")],
    prevent_initial_call=True
)
def update_bar_plot(selected_nuggets, selected_courses, start_date, end_date, n_clicks, reset_click):
    filtered_df = df

    if selected_nuggets:
        filtered_df = filtered_df[filtered_df['nuggetName'].isin(selected_nuggets)]

    if selected_courses:
        filtered_df = filtered_df[filtered_df['coursename'].isin(selected_courses)]

    if start_date and end_date:
        start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
        filtered_df = filtered_df[
            (filtered_df['day'] >= start_date.date()) & (filtered_df['day'] <= end_date.date())
        ]

    # Create a clean DataFrame using pd.groupby and pd.unstack
    counts = filtered_df.groupby(['day', 'nuggetName']).size().unstack(fill_value=0)

    # Create bar plot
    fig = px.bar(
        counts.reset_index(),
        x='day',
        y=selected_nuggets if selected_nuggets else counts.columns,  # If no nugget is selected, use all columns
        barmode='stack',
        labels={'day': 'Date', 'value': 'Count', 'variable': 'Learning Nugget'},
    )
    # Adjust legend font size
    fig.update_layout(
        legend=dict(
            title='',
            font=dict(size=10),  # Adjust the font size as needed
            orientation='v',  # Place legend horizontally
            yanchor='middle',  # Anchor legend to the bottom
            y=0.5,  # Adjust the y position
            xanchor='right',  # Anchor legend to the right
            x=5,  # Adjust the x position
        )
    )

    # Enable hover information
    fig.update_traces(hovertemplate='Day: %{x}<br>Count: %{y}')

    if n_clicks % 2 == 0:
        fig.update_layout(showlegend=False)
    else:
        fig.update_layout(showlegend=True)


    return fig


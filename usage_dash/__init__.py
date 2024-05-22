import dash
from dash import html, dcc, Output, Input, dash_table, ctx
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
import pandas as pd
import dash_bootstrap_components as dbc
from datetime import datetime
from dataset import import_dataset


df = import_dataset()


def create_usage_board(flask_app):
    dash_app = dash.Dash(__name__, server=flask_app, url_base_pathname="/dash/graphs/usage/", meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                         external_stylesheets=[dbc.themes.BOOTSTRAP, "/static/styles.css"])
    

    # Define DataTable style
    data_table_style = {
        'font-family': 'Arial, sans-serif',
        'font-size': '14px',
        'text-align': 'left',
        'margin-left': 'auto',
        'margin-right': 'auto'
    }

    # Define header style
    header_style = {
        'font-family': 'Arial, sans-serif',
        'backgroundColor': '#f2f2f2',
        'fontWeight': 'bold',
        'text-align': 'center'
    }

    # Define row style
    row_style = {
        'backgroundColor': '#ffffff'
    }

    # Define selected row style
    selected_row_style = {
        'backgroundColor': '#7bb9f6'
    }

    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(248, 248, 248)'
        },
        {
            'if': {'row_index': 'even'},
            'backgroundColor': 'white'
        },
        {
            'if': {'column_id': 'Aufrufe'},
            'color': 'black'
        }
    ]

    @dash_app.callback(
        Output('hidden-div', 'children'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_data_callback(n_intervals):
        global df
        df = import_dataset()
        return None


    def extract_academic_years(df):
        years = pd.to_datetime(df['day']).dt.year.unique()
        academic_years = [f"{year}/{year + 1}" for year in years]
        print(academic_years)
        return academic_years
    

    #TODO: Should I add the update data to routes instead of here?
    #TODO: Debug why scheduling is not properly working in Production
    #TODO: Add the live updates


    def usage_filters():
        """
        :return: A Div containing controls for graphs.
        """

        if df is None:
            print("DataFrame is None. Data fetching may have failed.")
            return html.Div("Error: Data fetching failed.")

        academic_years = extract_academic_years(df)

        current_date = datetime.now()

        if current_date.month >= 9:  # If the current month is September or later, consider the academic year as the current year + 1
            current_academic_year = f"{current_date.year}/{current_date.year + 1}"
        else:  # Otherwise, consider the academic year as the current year
            current_academic_year = f"{current_date.year - 1}/{current_date.year}"
    

        return html.Div(
            id="control-card",
            children=[
                html.H4("Bitte wählen Sie Ihre Filter aus", style={'textAlign': 'center'}),
                # Select year
                html.P("Studienjahr auswählen*"),
                dcc.Dropdown(
                    id="academic-year",
                    options=[],
                    value=current_academic_year,
                ),
                html.Br(),
                html.P("Semester auswählen*"),
                dcc.Checklist(
                id='semester-checklist',
                options=[
                    {'label': 'Winter Semester', 'value': 'Winter Semester'},
                    {'label': 'Sommer Semester', 'value': 'Sommer Semester'}
                ],
                value=['Winter Semester', 'Sommer Semester'],
                inline=True,
                style={'margin-bottom': '10px'}  # Adding space below the checklist
            ),
                html.Br(),
                # Select course
                html.P("Kurs auswählen*"),
                dcc.Dropdown(
                    id='course-dropdown',
                    options=[{'label': course, 'value': course} for course in df['coursename'].unique()],
                    multi=True,
                    placeholder='Kurs auswählen'
                ),
                html.Br(),
                # Select Topic
                html.P("Learning Block auswählen"),
                dcc.Dropdown(
                    id="LB-select",
                    placeholder='Learning Block auswählen',
                    multi=True,
                ),
                html.Br(),
                # Select Specific LN
                html.P("Learning Nugget auswählen"),
                dcc.Dropdown(
                    id='nugget-dropdown',
                    multi=True,
                    placeholder='Learning Nugget auswählen',
                    # style={'whiteSpace': 'nowrap'}
                ),
                html.Br(),
                # Select Difficulty
                html.P("Learning Nugget Schwierigkeit"),
                dcc.Dropdown(
                    id="diffic-select",
                    options=[{'label': diffic, 'value': diffic} for diffic in df['difficulty'].unique()],
                    multi=True,
                ),
                html.Br(),
                # Select day range
                html.P("Datum auswählen"),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=df['day'].min(),
                    end_date=df['day'].max(),
                    display_format='DD.MM.YYYY',
                    style={'border': 0}
                ),
                html.Br(),
                html.Br(),
                html.P("Anzahl der eindeutigen Nutzer zählen"),
                daq.BooleanSwitch(
                    id='unique-counts-switch',
                    on=True,
                    style={'margin-bottom': '10px'}
                ),
                html.Div([
                    #html.Div(
                    #    id="reset-btn-outer",
                    #    children=dbc.Button(id="reset-btn", color="secondary",children="Reset", n_clicks=0),
                    #    style={'float': 'right', 'margin-right': '20px'}
                    #),
                    #html.Div(
                    #    id="update-data-btn-outer",
                    #    children=dbc.Button(id="update-data-btn", color="secondary", children="Daten aktualisieren", n_clicks=0),
                    #    style={'float': 'right', 'margin-right': '20px'}
                    #)
                ],
                    className='row'
                ),
            ],
        )


    dash_app.layout = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(usage_filters(), md=4),  # Left column
                    dbc.Col(
                        [
                            # LN Usage graph
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.B("Learning Nugget Nutzung")),
                                    dbc.CardBody([dcc.Graph(id="bar-plot")])
                                ]
                            ),
                            html.Br(),
                            dbc.Button("Legende anzeigen/ausblenden", id="legend-toggle-btn", color="primary", className="mb-3"),
                            # Usage per Learning Nugget table
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.B("Nutzung pro Learning Nugget")),
                                    dbc.CardBody(
                                        [
                                            dash_table.DataTable(
                                                id="table",
                                                columns=[
                                                    {"name": "Learning Nugget", "id": "nuggetName"},
                                                    {"name": "Aufrufe", "id": "Aufrufe"},
                                                ],
                                                data=df.to_dict('records'),
                                                style_table={'overflowX': 'auto'},
                                                export_format="xlsx",
                                                export_headers='display',
                                                style_data=data_table_style,
                                                style_header=header_style,
                                                style_cell={'textAlign': 'center', 'padding': '10px'},
                                                style_cell_conditional=[
                                                    {'if': {'column_id': 'nuggetName'}, 'width': '50%'},
                                                    {'if': {'column_id': 'Aufrufe'}, 'width': '50%'},
                                                ],
                                                style_as_list_view=True,
                                                selected_rows=[],
                                                style_data_conditional=style_data_conditional,
                                                page_action='native',
                                                page_size=10,
                                            )
                                        ]
                                    )
                                ]
                            )
                        ],
                        md=8  # Right column
                    ),
                ]
            ),
            html.Div(id='hidden-div', style={'display': 'none'}),
            html.Div(id='hidden-div2', style={'display': 'none'}),
            # Interval component for data update
            dcc.Interval(
                id='interval-component',
                interval=60000,  # in milliseconds (update every minute)
                n_intervals=0
            )
        ],
        fluid=True,
    )


    @dash_app.callback(
        Output('academic-year', 'options'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_academic_year_options(n_intervals):
        if df is None:
            return [{'label': 'Error: Data fetching failed', 'value': None}]

        academic_years = extract_academic_years(df)
        print(academic_years)

        options = [{'label': year, 'value': year} for year in academic_years]

        return options

    @dash_app.callback(
        Output('course-dropdown', 'options'),
        [
            Input('semester-checklist', 'value')
        ]
    )
    def update_course_options(selected_semester):
        filtered_df = df.copy()

        # Filter data based on selected semester
        if selected_semester:
            if 'Winter Semester' in selected_semester and 'Sommer Semester' not in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Winter Semester"]
            elif 'Winter Semester' not in selected_semester and 'Sommer Semester' in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Sommer Semester"]
            else:
                filtered_df

        # Update options for courses
        course_options = [{'label': course, 'value': course} for course in filtered_df['coursename'].unique()]

        return course_options


    @dash_app.callback(
        [
            Output('LB-select', 'options'),
            Output('nugget-dropdown', 'options')
        ],
        [
            Input('course-dropdown', 'value'),
            Input('LB-select', 'value'),
            Input('diffic-select', 'value')
        ]
    )
    def update_options(selected_courses, selected_LB, selected_diffic):
        if not selected_courses:
            # If no courses are selected, return empty options for LB and nuggets
            return [], []

        filtered_df = df[df['coursename'].isin(selected_courses)]

        lb_options = [{'label': lb, 'value': lb} for lb in filtered_df['name'].unique()]
        nugget_options = [{'label': nugget, 'value': nugget} for nugget in filtered_df['nuggetName'].unique()]

        if selected_LB:
        # If learning blocks are selected, filter the DataFrame based on them
            filtered_df = filtered_df[filtered_df['name'].isin(selected_LB)]

        if selected_diffic:
        # If difficulties are selected, filter the DataFrame based on them
            filtered_df = filtered_df[filtered_df['difficulty'].isin(selected_diffic)]
    
    # Extract unique learning nuggets from the filtered DataFrame
        nugget_options = [{'label': nugget, 'value': nugget} for nugget in filtered_df['nuggetName'].unique()]

        return lb_options, nugget_options



    # Modify the callback to use the selected_date_range
    @dash_app.callback(
        Output('bar-plot', 'figure'),
        [Input('nugget-dropdown', 'value'),
        Input('course-dropdown', 'value'),
        Input('LB-select', 'value'),
        Input('diffic-select', 'value'),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date'),
        Input('legend-toggle-btn', 'n_clicks'),
        #Input("reset-btn", "n_clicks"),
        Input('academic-year', 'value'),
        Input('semester-checklist', 'value'),
        Input('unique-counts-switch', 'on')],
        prevent_initial_call=True
    )
    def update_bar_plot(selected_nuggets, selected_courses, selected_LB, selected_diffic, start_date, end_date, n_clicks, academic_year,
                        selected_semester, unique_counts):
        print("Callback triggered.")

        # if reset_click:
        #    # Reset filters to default values
        #    default_start_date = df['day'].min()
        #    default_end_date = df['day'].max()
        #    default_start_date_str = default_start_date.strftime('%Y-%m-%d')
        #    default_end_date_str = default_end_date.strftime('%Y-%m-%d')

        # Return an empty figure dictionary
        #    return {'data': [], 'layout': {}}

        filtered_df = df.copy()

        if academic_year and academic_year != 'All':
            start_date_range = pd.to_datetime(f'01-10-{academic_year.split("/")[0]}', format='%d-%m-%Y', dayfirst=True)
            end_date_range = pd.to_datetime(f'30-09-{academic_year.split("/")[1]}', format='%d-%m-%Y',
                                            dayfirst=True) + pd.DateOffset(days=1)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date_range.date()) & (filtered_df['day'] < end_date_range.date())
                ]

        if selected_semester:
            if 'Winter Semester' in selected_semester and 'Sommer Semester' not in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Winter Semester"]
            elif 'Winter Semester' not in selected_semester and 'Sommer Semester' in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Sommer Semester"]
            else:
                filtered_df

        if selected_nuggets:
            filtered_df = filtered_df[filtered_df['nuggetName'].isin(selected_nuggets)]

        if selected_courses:
            filtered_df = filtered_df[filtered_df['coursename'].isin(selected_courses)]

        if selected_LB:
            filtered_df = filtered_df[filtered_df['name'].isin(selected_LB)]    

        if selected_diffic:
            filtered_df = filtered_df[filtered_df['difficulty'].isin(selected_diffic)]

        if start_date and end_date:
            start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date.date()) & (filtered_df['day'] <= end_date.date())
                ]

        # Create a clean DataFrame using pd.groupby and pd.unstack
        if unique_counts:
            counts = filtered_df.groupby(['day', 'nuggetName'])['user_id'].nunique().unstack(fill_value=0)
        else:
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

        # Add a conditional check to handle the case when n_clicks is None
        if n_clicks is not None:
            if n_clicks % 2 == 0:
                fig.update_layout(showlegend=False)
            else:
                fig.update_layout(showlegend=True)

        return fig


    @dash_app.callback(Output('table', 'data'),
            [Input('nugget-dropdown', 'value'),
            Input('course-dropdown', 'value'),
            Input('LB-select', 'value'),
            Input('diffic-select', 'value'),
            Input('date-picker-range', 'start_date'),
            Input('date-picker-range', 'end_date'),
            Input('legend-toggle-btn', 'n_clicks'),
            #Input("reset-btn", "n_clicks"),
            Input('academic-year', 'value'),
            Input('semester-checklist', 'value'),
            Input('unique-counts-switch', 'on')],
        prevent_initial_call=True
    )
    def update_table_data(selected_nuggets, selected_courses, selected_LB, selected_diffic, start_date, end_date, n_clicks, academic_year,
                        selected_semester, unique_counts):

        filtered_df = df.copy()

        if academic_year and academic_year != 'All':
            start_date_range = pd.to_datetime(f'01-10-{academic_year.split("/")[0]}', format='%d-%m-%Y', dayfirst=True)
            end_date_range = pd.to_datetime(f'30-09-{academic_year.split("/")[1]}', format='%d-%m-%Y',
                                            dayfirst=True) + pd.DateOffset(days=1)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date_range.date()) & (filtered_df['day'] < end_date_range.date())
                ]

        if selected_semester:
            if 'Winter Semester' in selected_semester and 'Sommer Semester' not in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Winter Semester"]
            elif 'Winter Semester' not in selected_semester and 'Sommer Semester' in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Sommer Semester"]
            else:
                filtered_df

        if selected_nuggets:
            filtered_df = filtered_df[filtered_df['nuggetName'].isin(selected_nuggets)]

        if selected_courses:
            filtered_df = filtered_df[filtered_df['coursename'].isin(selected_courses)]

        if selected_LB:
            filtered_df = filtered_df[filtered_df['name'].isin(selected_LB)]

        if start_date and end_date:
            start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date.date()) & (filtered_df['day'] <= end_date.date())
                ]

        if selected_diffic:
            filtered_df = filtered_df[filtered_df['difficulty'].isin(selected_diffic)]


        # Count unique users if switch is on
        if unique_counts:
            counts = filtered_df.groupby(['nuggetName'])['user_id'].nunique().sort_values(ascending=False)
        else:
            counts = filtered_df.groupby(['nuggetName']).size().sort_values(ascending=False)

        data = pd.DataFrame({'nuggetName': counts.index, 'Aufrufe': counts.values}).to_dict('records')

        return data
    
       
    return dash_app

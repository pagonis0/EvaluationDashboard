import dash
from dash import html, dcc, Output, Input, dash_table, no_update
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
import pandas as pd
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from dataset import import_dataset
import diskcache as dc
import logging, threading, time, json, textwrap, os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

# Initialize the cache
cache = dc.Cache('./cache')

CACHE_KEY = 'dataset'
DATA_EXPIRE = 10*60

# Function to import dataset with caching
def get_dataset():
    try:
        logging.info("Attempting to load dataset")
        csv_file = '/app/dataset.csv'
        csv_last_modified = os.path.getmtime(csv_file)

        cached_data = cache.get(CACHE_KEY)
        cached_csv_last_modified = cache.get('csv_last_modified')

        if cached_data is None or cached_csv_last_modified != csv_last_modified:
            dataset = import_dataset()
            cache.set(CACHE_KEY, dataset, expire=DATA_EXPIRE) 
            cache.set('csv_last_modified', csv_last_modified)
            logging.info("Dataset loaded and cached")
        else:
            dataset = cached_data
            logging.info("Using cached dataset")
    except Exception as e:
        logging.error(f"Failed to load dataset: {str(e)}")
        raise

    return dataset


def create_usage_board(flask_app):
    df = get_dataset()

    dash_app = dash.Dash(__name__, server=flask_app, routes_pathname_prefix="/dash/graphs/usage/", requests_pathname_prefix="/eval/dash/graphs/usage/", meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                         external_stylesheets=[dbc.themes.BOOTSTRAP, "/eval/flaskdash/static/styles.css"])
    dash_app.config.suppress_callback_exceptions = True


    with open('metadata_cache.json', 'r') as f:
        data = json.load(f)

    flat_data = [item for sublist in data for item in sublist]    

    meta_module = pd.json_normalize([item['module_base_info'] for item in flat_data])
    meta_course = pd.json_normalize([item['course_info'] for item in flat_data])
    meta_module = meta_module.drop(['id', 'visible', 'name'], axis=1)
    meta = pd.concat([meta_module, meta_course], axis=1)
    
    total_LN_counts = meta.groupby('id')['content_name'].nunique()
    total_LN_counts_dict = total_LN_counts.to_dict()

    LN_used_counts = df.groupby('courseid')['nuggetName'].nunique()
    LN_used_counts_dict = LN_used_counts.to_dict()

    course_names = df.groupby('courseid')['coursename'].unique()
    course_names_dict = {course_id: list(names) for course_id, names in course_names.items()}


    data = []

    for course_id, course_name_list in course_names_dict.items():
        course_name = course_name_list[0]  # Assuming one name per course ID
        total_activities = total_LN_counts_dict.get(course_id, 0)
        used_activities = LN_used_counts_dict.get(course_id, 0)
        unused_activities = total_activities - used_activities
        
        if total_activities > 0:
            used_perc = (used_activities / total_activities) * 100
            unused_perc = (unused_activities / total_activities) * 100
        else:
            used_perc = 0
            unused_perc = 0
        
        data.append({
            "course_id": course_id,
            "course_name": course_name,
            "total_activities": total_activities,
            "used_activities": used_activities,
            "unused_activities": unused_activities,
            "used_perc": used_perc,
            "unused_perc": unused_perc
        })

    df_activity_usage = pd.DataFrame(data, columns=["course_id", "course_name", "total_activities", "used_activities", "unused_activities", "used_perc", "unused_perc"])


    data_table_style = {
        'font-family': 'Arial, sans-serif',
        'font-size': '14px',
        'text-align': 'left',
        'margin-left': 'auto',
        'margin-right': 'auto'
    }

    header_style = {
        'font-family': 'Arial, sans-serif',
        'backgroundColor': '#f2f2f2',
        'fontWeight': 'bold',
        'text-align': 'center'
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
        Output('hidden-div2', 'children'),
        [Input('interval-component', 'n_intervals')]
    )
    def update_data_callback(n):
        if n:
            df = get_dataset()
        logging.info(f"Dataset updated automatically in Dash app, {str(datetime.now())}")
        return None



    def extract_academic_years(df):
        years = pd.to_datetime(df['day']).dt.year.unique()
        academic_years = [f"{year}/{year + 1}" for year in years]
        return academic_years


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
                style={'margin-bottom': '10px'},
                labelStyle={'margin-right': '15px'}  # Adding space below the checklist
            ),
                html.Br(),
                # Select course
                html.P("Kurs auswählen*"),
                dcc.Dropdown(
                    id='course-dropdown',
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
                # Select Type
                html.P("Learning Nugget Type"),
                dcc.Dropdown(
                    id="type-select",
                    multi=True,
                ),
                html.Br(),
                # Select day range
                html.P("Datum auswählen"),
                dcc.DatePickerRange(
                    id='date-picker-range',
                    start_date=datetime.today()-timedelta(days=45),
                    end_date=datetime.today(),
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
                html.A(
                        id="update-data-btn-outer",
                        children=dbc.Button(id="update-data-btn", color="secondary", children="Daten aktualisieren", n_clicks=0),
                    ),
                html.Div([
                    dcc.Interval(
                        id='interval-component',
                        interval=10 * 60 * 1000,  # 10 minutes in milliseconds
                        n_intervals=0
                    ),
                    html.Div(id='hidden-div', style={'display': 'none'}),
                    html.Div(id='hidden-div2', style={'display': 'none'})
                ])
            ],
            style={
                'padding': '20px',
                'border': '1px solid #ccc',
                'border-radius': '5px',
                'background-color': '#f9f9f9',
                'box-shadow': '0 2px 4px rgba(0,0,0,0.1)',
                'font-family': 'Arial, sans-serif',
                'font-size': '14px',
                'color': '#333'
            }
        )


    dash_app.layout = dbc.Container(
        [
            dbc.Row(
                [    
                    dbc.Col(usage_filters(), md=4), 
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.B("Learning Nugget Nutzung")),
                                    dcc.Loading(
                                        id="loading-main-chart",
                                        children=[
                                            dbc.Card(
                                                dbc.CardBody([dcc.Graph(id="bar-plot")])
                                            )
                                        ],
                                        type="default"
                                    ),
                                    dcc.Loading(
                                        id="loading-pie-chart",
                                        children=[
                                            dbc.Card(
                                                dcc.Graph(id='activity-usage-pie-chart'),
                                                id="pie-chart-card",
                                                style={'display': 'none'}
                                            )
                                        ],
                                        type="default"
                                    )
                                ]
                            ),
                            html.P("Sicht:"),
                            dcc.Dropdown(
                                id='view-dropdown',
                                options=[
                                    {'label': 'Kurs', 'value': 'course'},
                                    {'label': 'Learning Block', 'value': 'LB'},
                                    {'label': 'Learning Nugget', 'value': 'nugget'},
                                    {'label': 'Learning Nugget typ', 'value': 'LN_type'},
                                    {'label': 'Schwierigkeit', 'value': 'difficulty'}
                                ],
                                value='course'
                            ),
                            html.Br(),
                            dbc.Button("Legende anzeigen/ausblenden", id="legend-toggle-btn", color="primary", className="mb-3"),
                            dbc.Collapse(
                            dbc.Card(
                                [
                                    dbc.CardHeader(html.B("Verwendete und Nicht Verwendete Aktivitäten")),
                                    dbc.CardBody([dcc.Graph(id='activity-usage-pie-chart')]),
                                ],
                                className="mb-3"
                            ),
                            id="pie-card",
                            is_open=False),
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
                        md=8 
                    ),
                ]
            ),
            dcc.Interval(
                id='interval-component',
                interval=1*60*1000, 
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
        global df 
        if n_intervals:
            df = get_dataset()
        
        academic_years = extract_academic_years(df)
        options = [{'label': year, 'value': year} for year in academic_years]

        return options
    
    @dash_app.callback(
        Output('pie-card', 'is_open'),
        [Input('course-dropdown', 'value')]
    )
    def toggle_pie_chart_card(active_cell):
        return bool(active_cell)

    @dash_app.callback(
        [
            Output('course-dropdown', 'options'),
            Output('LB-select', 'options'),
            Output('nugget-dropdown', 'options'),
            Output('type-select', 'options')
        ],
        [
            Input('academic-year', 'value'),
            Input('semester-checklist', 'value'),
            Input('date-picker-range', 'start_date'),
            Input('date-picker-range', 'end_date'),
            Input('course-dropdown', 'value'),
            Input('LB-select', 'value'),
            Input('type-select', 'value'),
            Input('interval-component', 'n_intervals')
        ]
    )
    def update_all_dropdowns(academic_year, selected_semester, start_date, end_date, selected_courses, selected_LB, selected_type, n_intervals):
        global df
        if df is None or n_intervals:
            df = get_dataset()

        filtered_df = df.copy()

        # Ensure start_date and end_date are converted to datetime objects
        if start_date is not None:
            start_date = pd.to_datetime(start_date).date()
        if end_date is not None:
            end_date = pd.to_datetime(end_date).date()
        
        # Apply the date filter on filtered_df['day']
        filtered_df = filtered_df[(filtered_df['day'] >= start_date) & (filtered_df['day'] <= end_date)]
        print("After date range filter:", filtered_df.shape)

        # Filter by semester
        if selected_semester:
            filtered_df = filtered_df[filtered_df['semester'].isin(selected_semester)]
            print("After semester filter:", filtered_df.shape)

        # Update course options based on current filters
        course_options = [{'label': course, 'value': course} for course in filtered_df['coursename'].unique()]
        print("Course options:", course_options)

        # If specific courses are selected, filter by them for LB options
        if selected_courses:
            filtered_df = filtered_df[filtered_df['coursename'].isin(selected_courses)]
            print("After course filter:", filtered_df.shape)

        # Update Learning Block options based on current filters
        lb_options = [{'label': lb, 'value': lb} for lb in filtered_df['name'].unique()]
        print("Learning Block options:", lb_options)

        # If specific Learning Blocks are selected, filter by them for nugget options
        if selected_LB:
            filtered_df = filtered_df[filtered_df['name'].isin(selected_LB)]
            print("After Learning Block filter:", filtered_df.shape)

        # Update Learning Nugget options based on current filters
        nugget_options = [{'label': nugget, 'value': nugget} for nugget in filtered_df['nuggetName'].unique()]
        print("Learning Nugget options:", nugget_options)

        if selected_type:
            filtered_df = filtered_df[filtered_df['type'].isin(selected_type)]

        type_options = [{'label': typ, 'value': typ} for typ in filtered_df['type'].unique()]
        print("Learning Nugget options:", type_options)

        return course_options, lb_options, nugget_options, type_options



    @dash_app.callback(
        Output('view-dropdown', 'options'),
        Output('view-dropdown', 'value'),
        [
            Input('course-dropdown', 'value'),
            Input('LB-select', 'value'),
            Input('view-dropdown', 'value')
        ],
        prevent_initial_call=True
    )
    def update_view_options(selected_courses, selected_LB, current_view):
        view_options = [
            {'label': 'Course', 'value': 'course'},
            {'label': 'Learning Block', 'value': 'LB'},
            {'label': 'Learning Nugget', 'value': 'nugget'},
            {'label': 'Learning Nugget Typ', 'value': 'type'},
            {'label': 'Schwierigkeit', 'value': 'difficulty'}
        ]
        
        default_view = 'course' 
        
        if selected_courses:
            view_options = [opt for opt in view_options if opt['value'] != 'course']
            default_view = 'LB'  
        
        if selected_LB:
            view_options = [{'label': 'Learning Nugget', 'value': 'nugget'},
                            {'label': 'Learning Nugget Typ', 'value': 'type'},
                            {'label': 'Schwierigkeit', 'value': 'difficulty'}]
            default_view = 'nugget' 

        
        if current_view not in [opt['value'] for opt in view_options]:
            current_view = default_view

        return view_options, current_view



    @dash_app.callback(
        Output('bar-plot', 'figure'),
        [
            Input('course-dropdown', 'value'),
            Input('LB-select', 'value'),
            Input('nugget-dropdown', 'value'),
            Input('academic-year', 'value'),
            Input('semester-checklist', 'value'),
            Input('date-picker-range', 'start_date'),
            Input('date-picker-range', 'end_date'),
            Input('unique-counts-switch', 'on'),
            Input('view-dropdown', 'value'),
            Input('legend-toggle-btn', 'n_clicks'),
            Input('interval-component', 'n_intervals'),
            Input('type-select', 'value')
        ],
        prevent_initial_call=True
    )
    def update_bar_plot(selected_courses, selected_LB, selected_nuggets, academic_year,
                        selected_semester, start_date, end_date, unique_counts, view, n_clicks, n_intervals, selected_type):
        global df 
        if n_intervals:
            df = get_dataset()
        
        filtered_df = df.copy()

        if academic_year and academic_year != 'All':
            start_date_range = pd.to_datetime(f'01-10-{academic_year.split("/")[0]}', format='%d-%m-%Y', dayfirst=True)
            end_date_range = pd.to_datetime(f'30-09-{academic_year.split("/")[1]}', format='%d-%m-%Y', dayfirst=True) + pd.DateOffset(days=1)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date_range.date()) & (filtered_df['day'] < end_date_range.date())
            ]

        if selected_semester:
            if 'Winter Semester' in selected_semester and 'Sommer Semester' not in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Winter Semester"]
            elif 'Winter Semester' not in selected_semester and 'Sommer Semester' in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Sommer Semester"]

        if selected_courses:
            filtered_df = filtered_df[filtered_df['coursename'].isin(selected_courses)]

        if selected_LB:
            filtered_df = filtered_df[filtered_df['name'].isin(selected_LB)]

        if selected_nuggets:
            filtered_df = filtered_df[filtered_df['nuggetName'].isin(selected_nuggets)]
        
        if selected_type:
            filtered_df = filtered_df[filtered_df['type'].isin(selected_type)]

        if start_date and end_date:
            start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date.date()) & (filtered_df['day'] <= end_date.date())
            ]

        # Dynamic grouping based on selection
        if view == 'course':
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'coursename'])['user_id'].nunique().unstack(fill_value=0)
            else:
                grouped_data = filtered_df.groupby(['day', 'coursename']).size().unstack(fill_value=0)
            x_label = 'Date'
            y_label = 'Course'
            legend_title = 'Course'
        elif view == 'LB':
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'name'])['user_id'].nunique().unstack(fill_value=0)
            else:
                grouped_data = filtered_df.groupby(['day', 'name']).size().unstack(fill_value=0)
            x_label = 'Date'
            y_label = 'Learning Block'
            legend_title = 'Learning Block'
        elif view == 'nugget': 
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'nuggetName'])['user_id'].nunique().unstack(fill_value=0)
            else:
                grouped_data = filtered_df.groupby(['day', 'nuggetName']).size().unstack(fill_value=0)
            x_label = 'Date'
            y_label = 'Learning Nugget'
            legend_title = 'Learning Nugget'
        elif view == 'type': 
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'type'])['user_id'].nunique().unstack(fill_value=0)
            else:
                grouped_data = filtered_df.groupby(['day', 'type']).size().unstack(fill_value=0)
            x_label = 'Date'
            y_label = 'Learning Nugget Typ'
            legend_title = 'Learning Nugget Typ'
        else: 
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'difficulty'])['user_id'].nunique().unstack(fill_value=0)
            else:
                grouped_data = filtered_df.groupby(['day', 'difficulty']).size().unstack(fill_value=0)
            x_label = 'Date'
            y_label = 'Learning Nugget Schwierigkeit'
            legend_title = 'Learning Nugget Schwierigkeit'

        fig = px.bar(
            grouped_data.reset_index(),
            x='day',
            y=grouped_data.columns,
            barmode='stack',
            labels={'day': 'Datum', 'value': 'Anzahl', 'variable': y_label},
        )

        fig.update_layout(
            legend=dict(
                title=legend_title, 
                orientation='v', 
                yanchor='middle', 
                y=0.5, 
                xanchor='right', 
                x=5,  
            )
        )

        fig.update_traces(hovertemplate='Day: %{x}<br>Count: %{y}')

        show_legend = n_clicks is None or n_clicks % 2 == 0
        fig.update_layout(showlegend=show_legend)

        return fig

    @dash_app.callback(
        Output('activity-usage-pie-chart', 'figure'),
        [Input('course-dropdown', 'value')]
    )
    def update_pie_chart(selected_courses):
        if not selected_courses:
            return go.Figure()

        filtered_df = df_activity_usage[df_activity_usage['course_name'].isin(selected_courses)]
        used_activities = filtered_df['used_activities'].sum()
        unused_activities = filtered_df['unused_activities'].sum()
        total_activities = filtered_df['total_activities'].sum()
        
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=['Genutzt Learning Nuggets', 'Ungenutzt Learning Nuggets'],
                    values=[used_activities, unused_activities],
                    hole=0.4,
                    marker=dict(colors=['#7bb9f6', '#f2f2f2']),
                    hoverinfo='label+percent+text',
                    text=[f'{used_activities} Genutzt', f'{unused_activities} Ungenutzt'],
                    textinfo='percent',
                    textposition='inside'
                )
            ]
        )

        if len(selected_courses) > 1:
            formatted_course_names = ', '.join(selected_courses[:-1]) + ' and ' + selected_courses[-1]
        else:
            formatted_course_names = selected_courses[0]
        title_text = f'Prozentsatz der verwendeten vs. nicht verwendeten Learning Nuggets im Kurs: {formatted_course_names}'
        title_lines = title_text.split(' ')
        max_words_per_line = 10
        wrapped_title = '<br>'.join([' '.join(title_lines[i:i + max_words_per_line]) for i in range(0, len(title_lines), max_words_per_line)])

        fig.update_layout(
            title={
                'text': wrapped_title,
                'font': {'size': 15},  
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
            },
            annotations=[
                dict(
                    text='Learning Nuggets',
                    x=0.5,
                    y=0.5,
                    font_size=10,
                    showarrow=False
                )
            ],
            margin=dict(t=120),
        )
        

        fig.add_annotation(
            x=0.5,
            y=1.10,  
            text=f'Gesam Learning Nugget Anzahl: {total_activities}',
            showarrow=False,
            xref="paper",
            yref="paper",
            font=dict(size=12),
            align="center"
        )
        
        return fig



    @dash_app.callback(
        [Output('table', 'data'),
        Output('table', 'columns')],
        [
            Input('course-dropdown', 'value'),
            Input('LB-select', 'value'),
            Input('nugget-dropdown', 'value'),
            Input('academic-year', 'value'),
            Input('semester-checklist', 'value'),
            Input('date-picker-range', 'start_date'),
            Input('date-picker-range', 'end_date'),
            Input('unique-counts-switch', 'on'),
            Input('view-dropdown', 'value'),
            Input('interval-component', 'n_intervals'),
            Input('type-select', 'value')
        ],
        prevent_initial_call=True
    )
    def update_table(selected_courses, selected_LB, selected_nuggets, academic_year,
                    selected_semester, start_date, end_date, unique_counts, view, n_intervals, selected_type):
        
        global df 
        if n_intervals:
            df = get_dataset()

        filtered_df = df.copy()

        if academic_year and academic_year != 'All':
            start_date_range = pd.to_datetime(f'01-10-{academic_year.split("/")[0]}', format='%d-%m-%Y', dayfirst=True)
            end_date_range = pd.to_datetime(f'30-09-{academic_year.split("/")[1]}', format='%d-%m-%Y', dayfirst=True) + pd.DateOffset(days=1)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date_range.date()) & (filtered_df['day'] < end_date_range.date())
            ]

        if selected_semester:
            if 'Winter Semester' in selected_semester and 'Sommer Semester' not in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Winter Semester"]
            elif 'Winter Semester' not in selected_semester and 'Sommer Semester' in selected_semester:
                filtered_df = filtered_df[filtered_df['semester'] == "Sommer Semester"]

        if selected_courses:
            filtered_df = filtered_df[filtered_df['coursename'].isin(selected_courses)]

        if selected_LB:
            filtered_df = filtered_df[filtered_df['name'].isin(selected_LB)]

        if selected_nuggets:
            filtered_df = filtered_df[filtered_df['nuggetName'].isin(selected_nuggets)]

        if selected_type:
            filtered_df = filtered_df[filtered_df['type'].isin(selected_type)]

        if start_date and end_date:
            start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
            filtered_df = filtered_df[
                (filtered_df['day'] >= start_date.date()) & (filtered_df['day'] <= end_date.date())
            ]

        if view == 'course':
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'coursename'])['user_id'].nunique().unstack(fill_value=0)
                sum_per_course = grouped_data.sum(axis=0).reset_index()
                sum_per_course.columns = ['coursename', 'course_calls']
                columns = [
                    {"name": "Kurs", "id": "coursename"},
                    {"name": "Kurs Aufrufe", "id": "course_calls"}
                ]
            else:
                grouped_data = filtered_df.groupby(['day', 'coursename']).size().unstack(fill_value=0)
                sum_per_course = grouped_data.sum(axis=0).reset_index()
                sum_per_course.columns = ['coursename', 'course_calls']
                columns = [
                    {"name": "Kurs", "id": "coursename"},
                    {"name": "Kurs Aufrufe", "id": "course_calls"}
                ]

            data = sum_per_course.to_dict('records')

        elif view == 'LB':
            if unique_counts:
                grouped_data = filtered_df.groupby(['name', 'coursename'])['user_id'].nunique().reset_index()
                sum_per_LB_course = grouped_data.groupby(['name', 'coursename'])['user_id'].sum().reset_index()
                sum_per_LB_course.columns = ['name', 'coursename', 'Aufrufe']
                columns = [
                    {"name": "Learning Block", "id": "name"},
                    {"name": "Kurs", "id": "coursename"},
                    {"name": "Learning Block Aufrufe", "id": "Aufrufe"}
                ]
            else:
                grouped_data = filtered_df.groupby(['name', 'coursename']).size().reset_index(name='Aufrufe')
                sum_per_LB_course = grouped_data.groupby(['name', 'coursename'])['Aufrufe'].sum().reset_index()
                columns = [
                    {"name": "Learning Block", "id": "name"},
                    {"name": "Kurs", "id": "coursename"},
                    {"name": "Learning Block Aufrufe", "id": "Aufrufe"}
                ]

            data = sum_per_LB_course.to_dict('records')


        elif view == 'nugget':
            if unique_counts:
                grouped_data = filtered_df.groupby(['nuggetName', 'name', 'coursename', 
                                                    'type', 'difficulty'])['user_id'].nunique().reset_index()
                sum_per_LN_course = grouped_data.groupby(['nuggetName', 'name', 'coursename', 
                                                    'type', 'difficulty'])['user_id'].sum().reset_index()
                sum_per_LN_course.columns = ['nuggetName', 'name', 'coursename', 'type', 'difficulty', 'Aufrufe']
                columns = [
                    {"name": "Learning Nugget", "id": "nuggetName"},
                    {"name": "Learning Block", "id": "name"},
                    {"name": "Kurs", "id": "coursename"},
                    {"name": "Aufrufe", "id": "Aufrufe"},
                    {"name": "Schwierikeit", "id": "difficulty"},
                    {"name": "Typ", "id": "type"}
                    
                ]
                columns = [
                    {"name": "Learning Nugget", "id": "nuggetName"},
                    {"name": "Learning Block", "id": "name"},
                    {"name": "Kurs", "id": "coursename"},
                    {"name": "Aufrufe", "id": "Aufrufe"},
                    {"name": "Schwierikeit", "id": "difficulty"},
                    {"name": "Typ", "id": "type"}
                ]
            else:
                grouped_data = filtered_df.groupby(['nuggetName', 'name', 'coursename', 
                                                    'type', 'difficulty'])['user_id'].size().reset_index(name='Aufrufe')
                sum_per_LN_course = grouped_data.groupby(['nuggetName', 'name', 'coursename', 
                                                    'type', 'difficulty'])['user_id'].sum().reset_index()
                sum_per_LN_course.columns = ['nuggetName', 'name', 'coursename', 'type', 'difficulty', 'Aufrufe']
                columns = [
                    {"name": "Learning Nugget", "id": "nuggetName"},
                    {"name": "Learning Block", "id": "name"},
                    {"name": "Kurs", "id": "coursename"},
                    {"name": "Learning Block Aufrufe", "id": "Aufrufe"},
                    {"name": "Schwierikeit", "id": "difficulty"},
                    {"name": "Typ", "id": "type"}
                    
                ]
                grouped_data = filtered_df.groupby(['nuggetName', 'coursename', 'name', 'type', 'difficulty']).agg(
                    Used_LNs=('user_id', 'nunique')
                ).reset_index()
                columns = [
                    {"name": "Learning Nugget Name", "id": "nuggetName"},
                    {"name": "Course Name", "id": "coursename"},
                    {"name": "Learning Block Name", "id": "name"},
                    {"name": "Type", "id": "type"},
                    {"name": "Difficulty", "id": "difficulty"},
                    {"name": "Used Learning Nuggets", "id": "Used_LNs"}
                ]

            data = sum_per_LN_course.to_dict('records')

        elif view == 'type':
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'type'])['user_id'].nunique().unstack(fill_value=0)
            else:
                grouped_data = filtered_df.groupby(['day', 'type']).size().unstack(fill_value=0)

            sum_per_type = grouped_data.sum(axis=0).reset_index()
            avg_calls_per_day = sum_per_type[0] / len(grouped_data)
            sum_per_type.columns = ['type', 'type_calls']
            sum_per_type['avg_calls_per_day'] = round(avg_calls_per_day, 2)

            columns = [
                {"name": "Learning Nugget Typ", "id": "type"},
                {"name": "Aufrufe", "id": "type_calls"},
                {"name": "Durchschnittliche Aufrufe pro Tag", "id": "avg_calls_per_day"}
            ]

            data = sum_per_type.to_dict('records')

        elif view == 'difficulty':
            if unique_counts:
                grouped_data = filtered_df.groupby(['day', 'difficulty'])['user_id'].nunique().unstack(fill_value=0)
            else:
                grouped_data = filtered_df.groupby(['day', 'difficulty']).size().unstack(fill_value=0)

            sum_per_difficulty = grouped_data.sum(axis=0).reset_index()
            avg_calls_per_day = sum_per_difficulty[0] / len(grouped_data)
            sum_per_difficulty.columns = ['difficulty', 'difficulty_calls']
            sum_per_difficulty['avg_calls_per_day'] = round(avg_calls_per_day, 2)

            columns = [
                {"name": "Learning Nugget Schwierigkeit", "id": "difficulty"},
                {"name": "Aufrufe", "id": "difficulty_calls"},
                {"name": "Durchschnittliche Aufrufe pro Tag", "id": "avg_calls_per_day"}
            ]

            data = sum_per_difficulty.to_dict('records')

        return data, columns
    
       
    return dash_app

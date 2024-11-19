import dash
from dash import html, dcc, Output, Input, dash_table, no_update, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('mode.chained_assignment', None)

def create_chatbot_board(flask_app):
    df = pd.read_csv('messages.csv')
    df['datetime'] = pd.to_datetime(df['datetime'])

    print("Data loaded successfully:")
    print(df.head())

    dash_app = dash.Dash(__name__, server=flask_app, routes_pathname_prefix="/dash/graphs/chatbot/", 
                         requests_pathname_prefix="/eval/dash/graphs/chatbot/", meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                         external_stylesheets=[dbc.themes.BOOTSTRAP, "/eval/flaskdash/static/styles.css"])
    dash_app.config.suppress_callback_exceptions = True

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

    style_data_conditional = [
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

    # Create basic dashboard using a dropdown from module to module
    dash_app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Chatbot Data Dashboard"), className="mb-2")
        ]),
        dbc.Row([
            dbc.Col(html.H6(children="Select Visualization:"), width=3)
        ]),
        dbc.Row([
            dbc.Col(
                # 5 Different visualisation options
                dcc.Dropdown(
                    id='visualization-dropdown',
                    options=[
                        {'label': '1. Message Count by Role', 'value': 'msg_count_role'}, # If questions are answered
                        {'label': '2. Message Frequency over Time', 'value': 'msg_freq_time'}, # How many messages sent per day
                        {'label': '3. Response Time', 'value': 'response_time'}, # How much time it takes to generate the answer
                        {'label': '4. Chat Length', 'value': 'chat_length'}, # How long is the chat
                        {'label': '5. Activity', 'value': 'activity'} # User activity
                    ],
                    value='msg_count_role',
                    clearable=False
                ),
                width=6
            )
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='visualization-graph'),
                width=12
            )
        ]),
        # Basic Table including the whole dataset
        # Currently unprocessed #TODO Process according to your needs
        dbc.Row([
            dbc.Col([
                html.H5("Data Table"),
                dash_table.DataTable(
                    id='data-table',
                    columns=[{"name": i, "id": i} for i in df.columns],
                    page_current=0,
                    page_size=10,
                    page_action='custom',
                    style_table=data_table_style,
                    style_cell={'textAlign': 'left', 'padding': '5px'},
                    style_header=header_style,
                    style_data_conditional=style_data_conditional
                )
            ], width=12)
        ])
    ], fluid=True)

    # Produce graphics
    @dash_app.callback(
        Output('visualization-graph', 'figure'),
        Input('visualization-dropdown', 'value')
    )
    def update_graph(selected_visualization):
        print(f"Selected visualization: {selected_visualization}")

        if selected_visualization == 'msg_count_role':
            role_counts = df['role'].value_counts().reset_index()
            role_counts.columns = ['Role', 'Count']
            fig = px.pie(role_counts, names='Role', values='Count',
                         title='Message Count by Role',
                         color='Role',
                         color_discrete_map={'USER': 'lightblue', 'EXPERT': 'orange'})
            fig.update_traces(textposition='inside', textinfo='percent+label')
            return fig

        elif selected_visualization == 'msg_freq_time':
            msg_freq = df.groupby(df['datetime'].dt.date)['message_id'].count().reset_index()
            msg_freq.columns = ['Date', 'Message Count']
            fig = px.line(msg_freq, x='Date', y='Message Count',
                          title='Message Frequency Over Time',
                          labels={'Date': 'Date', 'Message Count': 'Number of Messages'})
            fig.update_traces(mode='markers+lines')
            return fig
        
        elif selected_visualization == 'response_time':
            resp_time = df[df['generation_info']!=None]
            resp_time = df['generation_info']
            fig = px.histogram(resp_time, title='Response Time')
            fig.update_layout(
            xaxis_title_text='Response Time (Seconds)', # xaxis label
            yaxis_title_text='Count', # yaxis label
            bargap=0.2, # gap between bars of adjacent location coordinates
            bargroupgap=0.1 # gap between bars of the same location coordinates
            )
            return fig

        elif selected_visualization == 'chat_length':
            df['datetime'] = pd.to_datetime(df['datetime'])
            df['date'] = df['datetime'].dt.date

            avg_chat_length = df.groupby(['date', 'role']).size().unstack(fill_value=0).sum(axis=1).rolling(7).mean()

            fig = px.line(avg_chat_length, x=avg_chat_length.index, y=avg_chat_length.values,
                        labels={'x': 'Date', 'y': 'Average Chat Length'},
                        title='Average Chat Length Over Time')
            fig.update_layout(showlegend=False)
            return fig


        elif selected_visualization == 'activity':
            fig = go.Figure()
            fig.update_layout(
                title="Activity Visualization Coming Soon",
                xaxis={'visible': False},
                yaxis={'visible': False},
                annotations=[{'text': "This feature is under development.", 'xref': "paper", 'yref': "paper", 'showarrow': False, 'font': {'size': 20}}]
            )
            return fig

        else:
            fig = go.Figure()
            fig.update_layout(title="Select a visualization from the dropdown menu.")
            return fig

    # Produce table
    @dash_app.callback(
        Output('data-table', 'data'),
        [Input('data-table', 'page_current'),
         Input('data-table', 'page_size')]
    )
    def update_table(page_current, page_size):
        start = page_current * page_size
        end = start + page_size
        return df.iloc[start:end].to_dict('records')

    return dash_app

# https://hackersandslackers.com/plotly-dash-with-flask/
# https://dash.plotly.com/external-resources
import json

from dash import Dash, html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
# from dash_extensions.enrich import DeferScript

from RecommendationSystem.makeGraphs import go_plot, default_fig
from RecommendationSystem.makeNetworks import section_path, get_diff, get_step


def dash_layout(s_id, max_steps, records, paths, init=False, compute_steps=False):

    # TODO: compute changes stepwise

    courses = []
    for path in paths:
        courses.extend([entry['course']['name'] for entry in path['courses']])
    courses = list(set(courses))
    print(" >> courses", courses)
    print(" >> records", records)
    print(" >> paths", paths)
    course = courses[0] if courses else None
    if init:
        difference_plot = default_fig()
    else:
        difference_plot = difference(n_steps=max_steps, paths=paths, records=records, course=course)
    print(" > Session:", s_id)
    return html.Div([
        dcc.Location(id="loc"),
        dcc.Store(id="session", data=s_id),
        dcc.Store(id="store", storage_type="memory", data={s_id:{"records": records, "paths": paths}}),
        html.Div(children=[
            html.Div(
                html.H1(children='Recommendation Steps', style={'textAlign': 'center'}),
                     style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '35vw', 'margin-top': '1vw'}
                     ),
            html.Div(children=[
                dbc.Button(children="Return", n_clicks=0, id="return",
                           style={'textAlign': 'right'}, color="primary"),
            ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '26vw', 'margin-top': '3vw'})
            ]),
        html.Div(children=[
            html.Div(children=[
                "Show ",
                dcc.Input(id='n_steps', value=max_steps, type='number', min=-max_steps, max=max_steps),
                " first steps"
            ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '1vw', 'margin-top': '3vw'}),
            html.Div(children=[
                "Course: ",
                dcc.Dropdown(options=courses, id='course', value=course, clearable=False)
            ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '20vw', 'margin-top': '3vw', 'width': '50%'}),
        ]),
        dcc.Graph(figure=difference_plot, style={'height': '75vh'}, id="paths"),
    ])


def dynamic_layout(session):

    # paths = session.get('recommendations')
    # records = session.get('record')
    # max_steps = len(records)

    #courses = []
    #for path in paths:
    #    courses.extend([entry['course']['name'] for entry in path['courses']])
    #courses = list(set(courses))
    #course = courses[0] if courses else None
    
    def serve_layout():
        return html.Div([
            dcc.Location(id="loc"),
            dcc.Store(id="store", storage_type="memory", data={session.get('id'):{"records": session.get('record'), "paths": session.get('recommendations')}}),
            html.Div(children=[
                html.Div(
                    html.H1(children='Recommendation Steps', style={'textAlign': 'center'}),
                        style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '35vw', 'margin-top': '1vw'}
                        ),
                html.Div(children=[
                    dbc.Button(children="Return", n_clicks=0, id="return",
                            style={'textAlign': 'right'}, color="primary"),
                ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '26vw', 'margin-top': '3vw'})
                ]),
            html.Div(children=[
                html.Div(children=[
                    "Show ",
                    dcc.Input(id='n_steps', value=len(session.get('record', [])), 
                              type='number', min=-len(session.get('record', [])), 
                              max=len(session.get('record', []))),
                    " first steps"
                ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '1vw', 'margin-top': '3vw'}),
                html.Div(children=[
                    "Course: ",
                    dcc.Dropdown(options=[course for _, course in session.get('enrolled', [])], 
                                 id='course', 
                                 value=session.get('enrolled')[0][1] if len(session.get('enrolled', [])) > 0 else "", 
                                 clearable=False
                                 )
                ], style={'display': 'inline-block', 'vertical-align': 'top', 'margin-left': '20vw', 'margin-top': '3vw', 'width': '50%'}),
            ]),
            dcc.Graph(figure=  # session.get('diff'),
                      difference(
                          n_steps=len(session.get('record', [])), 
                          paths=session.get('recommendations'), 
                          records=session.get('record'), 
                          course=session.get('enrolled')[0][1] if len(session.get('enrolled', [])) > 0 else None), 
                      style={'height': '75vh'}, id="paths"),
        ])
    return serve_layout
    

def init_dash(server, session):

    app = Dash(__name__, 
               server=server, url_base_pathname=f"/steps/",
               external_stylesheets=[{
                   "rel": "stylesheet",
                   "href": 'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css',
                   "integrity": "sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T",
                   "crossorigin": "anonymous"}],
               external_scripts=[
                     {"src": "https://polyfill.io/v3/polyfill.min.js?features=es6", },
                     {"id": "MathJax-script",
                      "src": "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"},
                     {"src": "https://code.jquery.com/jquery-3.3.1.slim.min.js",
                      "integrity": "sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo",
                      "crossorigin": "anonymous"},
                     {"src": "https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js",
                      "integrity": "sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1",
                      "crossorigin": "anonymous"},
                     {"src": "https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js",
                      "integrity": "sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM",
                      "crossorigin": "anonymous"},
                     {"src": "https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js",
                      "integrity": "sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl",
                      "crossorigin": "anonymous"},
                     {"src": "https://cdn.plot.ly/plotly-latest.min.js"},
                     {"type": "text/javascript",
                      "charset": "utf8",
                      "src": "https://code.jquery.com/jquery-3.6.0.min.js"},
                     {"type": "text/javascript",
                      "charset": "utf8",
                      "src": "https://cdn.datatables.net/1.13.1/js/jquery.dataTables.js"},
                     {"type": "text/javascript",
                      "charset": "utf8",
                      "src": "https://cdn.datatables.net/1.10.25/js/dataTables.bootstrap5.js"}],
               suppress_callback_exceptions=True)

    max_steps = 0
    app.layout = dash_layout(None, max_steps, records=[], paths=[], init=True)
    app.layout = dynamic_layout(session)

    return app


def difference_test(n_steps=0):
    steps = ["S_26", "S_27", "S_0", "S_19", "S_138"]
    if not n_steps:
        return default_fig()
    elif n_steps > abs(len(steps)):
        n_steps = len(steps)
        step_range = range(n_steps)
    elif n_steps < 0:
        step_range = range((len(steps)+n_steps), len(steps))
    else:
        step_range = range(n_steps)
    course = ""
    graphs = []
    diffs = []
    steps_from = []
    prev_path = None
    for t in step_range:

        with open(f"../sample_rec_{t}.json", "r") as jf:
            j = json.load(jf)

        course = j["courses"][0]["course"]["name"]
        path = j["courses"][0]["section_path"]

        step = {"id": t, "name": f"step_{t}", "grade": 0, "section": steps[t]}

        current = section_path(path, t=t, step=step)
        graphs.append(current)

        if prev_path:
            diff = get_diff(prev_path, current)
            diffs.append(diff)
            step_from = get_step(prev_path, step, t)
            steps_from.append(step_from)
        prev_path = current

    diff_plot = go_plot(graphs, diffs, course, steps_from)
    return diff_plot


def difference(n_steps, paths, records, course):

    print(" >> in difference()")
    print("- n_steps:", n_steps)
    print("- paths:\n  ", paths)
    print("- records:\n  ", records)
    print("- course:", course)
    if not n_steps or not course or len(paths)==0:
        return default_fig()
    
    n_steps = int(n_steps)
    course = int(course)
    if records == None:
        records = [{'id': 0, 'name': '<start>', 'grade': 0, 'section': ''}]
    if n_steps > abs(len(records)):
        n_steps = len(records)
        step_range = range(n_steps)
    elif n_steps < 0:
        step_range = range((len(records)+n_steps), len(records))
    else:
        step_range = range(n_steps)

    graphs = []
    diffs = []
    steps_from = []
    prev_path = None

    for t in step_range:

        # print(" >> Path t:")
        # print(paths[t])
        for course_path in paths[t]["courses"]:
            course_id = course_path['course']['id']
            print(f"{course_id} == {course} : {course_id == course}")
            if course_id == course:
                # course = paths[t]["courses"][0]["course"]["name"]
                # path = paths[t]["courses"][0]["section_path"]
                path = course_path["section_path"]

                step = records[t]

                current = section_path(path, t=t, step=step)
                graphs.append(current)

                if prev_path:
                    diff = get_diff(prev_path, current)
                    diffs.append(diff)
                    step_from = get_step(prev_path, step, t)
                    steps_from.append(step_from)
                prev_path = current

            # break  # no need to keep iterating over courses if correct one found

    diff_plot = go_plot(graphs, diffs, course, steps_from)
    return diff_plot


@callback(
    Output(component_id="paths", component_property="figure"),
    [Input(component_id="n_steps", component_property="value"),
     Input(component_id="course", component_property="value"),
     State(component_id="session", component_property="data")])
def update_diff_steps(n_steps, course, session, store):
    print(" >> update diff steps", n_steps, course, store)
    print(" > Session:", session)
    return difference(n_steps, session['paths'], session['records'], course)


@callback(
    Output(component_id="loc", component_property="href"),
    Input(component_id="return", component_property="n_clicks"))
def bttn_return(n_clicks):
    if n_clicks > 0:
        return "/recommendation"


def _compute_steps():
    # TODO
    pass

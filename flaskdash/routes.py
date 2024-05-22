from flask import render_template, send_file
from flaskdash import app
import json, os, requests, datetime, hashlib
import pandas as pd
import plotly.graph_objs as go
from flaskdash.forms import DownloadForm
from events_process.events import EventHandling
from dataset import import_dataset
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

df = import_dataset()

df['day'] = pd.to_datetime(df['day'])

courses = df['courseid'].nunique()
users = df['user_id'].nunique()
lns = df['content_name'].nunique()


duplicate_columns = df.columns[df.columns.duplicated()]

def hash_user_id(user_id):
    hashed_id = hashlib.sha256(str(user_id).encode()).hexdigest()
    return hashed_id

def generate_academic_year(date):
    if date.month >= 10:
        return f"{date.year}/{date.year + 1}"
    else:
        return f"{date.year - 1}/{date.year}"

df['academic_year'] = df['day'].apply(generate_academic_year)

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", courses=courses, lns=lns, users=users)

@app.route("/nutzung")
def nutzung():
    return render_template("nutzung.html")

@app.route("/noten")
def noten():
    return render_template("working.html")

@app.route("/downloads", methods=['GET', 'POST'])
def download():
    form = DownloadForm()

    academic_year_choices = [(year, year) for year in df['academic_year'].unique()]
    form.academic_year.choices = academic_year_choices
    
    semester_choices = [(semester, semester) for semester in df['semester'].unique()]
    semester_choices.insert(0, ("Alle", "Alle"))
    form.semester.choices = semester_choices

    course_choices = [(course, course) for course in df['coursename'].unique()]
    form.course.choices = course_choices
    
    if form.validate_on_submit():

        academic_year_selected = form.academic_year.data
        semester_selected = form.semester.data
        course_selected = form.course.data

        filtered_df = df.copy() 
        
        if semester_selected != "Alle":
            filtered_df = filtered_df[filtered_df['semester'] == semester_selected]

        filtered_df = filtered_df[filtered_df['academic_year'] == academic_year_selected]

        if course_selected:
            filtered_df = filtered_df[filtered_df['coursename'] == course_selected]

        user_mapping = {}
        pseudoanonymized_ids = []

        for user_id in filtered_df['user_id']:
            hashed_id = hash_user_id(user_id)
            pseudoanonymized_ids.append(hashed_id)
            user_mapping[user_id] = hashed_id

        filtered_df['user_id'] = pseudoanonymized_ids

        filtered_df = filtered_df.drop(["anonymous", "component", "contextid", "contextinstanceid", "crud", "edulevel", "eventname",
                                        "lectureDate", "objectid", "others", "quizid", "recourceFiletype",
                                        "relateduserid", "scromHighestGrade", "scromId", "scromNeeded","target", "year-week",
                                        "id", "course", "module", "instance", "is_ln", "resp_id", "contextlevel"], axis=1)
        save_dir = os.path.join(os.getcwd(), 'flaskdash')  # Change 'flaskdash' to your desired folder name

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        excel_file = os.path.join(save_dir, f'data_{datetime.datetime.now()}.xlsx')
        filtered_df.to_excel(excel_file, index=False)

        response = send_file(excel_file, as_attachment=True)

        os.remove(excel_file)

        return response
        
    return render_template('download.html', form=form)


# Define your Plotly graphs
def generate_plotly_graphs():
    graph1 = go.Scatter(x=[1, 2, 3], y=[4, 1, 2], mode='lines', name='Graph 1')
    graph2 = go.Bar(x=[1, 2, 3], y=[2, 5, 3], name='Graph 2')
    # Add more graphs as needed
    return [graph1, graph2]

# Convert Plotly graphs to JSON-compatible dictionaries
def graphs_to_json(graphs):
    json_graphs = []
    for graph in graphs:
        json_graphs.append(graph.to_plotly_json())
    return json_graphs

# Define your Flask route
@app.route('/test')
def test():
    print(EventHandling().api_call())
    graphs = generate_plotly_graphs()
    graphs_json = graphs_to_json(graphs)
    graphs_with_index = [(index, graph_json) for index, graph_json in enumerate(graphs_json)]
    return render_template('test.html', graphs=graphs_with_index)



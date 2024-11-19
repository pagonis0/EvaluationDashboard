from flask import render_template, send_file, Blueprint, current_app
import requests, hashlib
import pandas as pd
import os, datetime,json
from DataFetcher.EventData import EventHandling
from FlaskDash.main.forms import DownloadForm
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import warnings

warnings.simplefilter('ignore', InsecureRequestWarning)

"""
The routes for the Flask component working with the main flask page and the download section.
"""

main = Blueprint('main', __name__)

def hash_user_id(user_id):
    hashed_id = hashlib.sha256(str(user_id).encode()).hexdigest()
    return hashed_id

def generate_academic_year(date):
    if date.month >= 10:
        return f"{date.year}/{date.year + 1}"
    else:
        return f"{date.year - 1}/{date.year}"

@main.route("/")
@main.route("/home")
def home():
    with current_app.config['data_lock']:
        df = current_app.config['data'].copy()
    df['academic_year'] = df['day'].apply(generate_academic_year)
    courses = df['courseid'].nunique()
    users = df['user_id'].nunique()
    lns = df['nuggetName'].nunique()
    metadata = []
    with open('/app/metadata_cache.json', 'r') as file:
        json_data = json.load(file)
        for data_list in json_data:
            for data in data_list:
                ln = pd.json_normalize(data['module_base_info']).drop(['id', 'visible', 'name'], axis=1, errors='ignore')
                metadata.append(ln)
                
    if metadata:
        result_df = pd.concat(metadata, ignore_index=True)
        all_lns = result_df['content_name'].nunique()
        return render_template("home.html", courses=courses, lns=lns, users=users, all_lns=all_lns)
    else:
        print("No valid metadata entries found.")
        return render_template("home.html", courses=courses, lns=lns, users=users, all_lns='Currently unavailiable')

@main.route("/downloads", methods=['GET', 'POST'])
def download():
    form = DownloadForm()

    with current_app.config['data_lock']:
        df = current_app.config['data'].copy()

    df['academic_year'] = df['day'].apply(generate_academic_year)

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

        filtered_df = filtered_df.drop(["objectid", "scromHighestGrade", "year-week",
                                        "course", "is_ln", "resp_id"], axis=1)
        save_dir = os.path.join(os.getcwd(), 'flaskdash') 
        
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        excel_file = os.path.join(save_dir, f'data_{datetime.datetime.now()}.xlsx')
        filtered_df.to_excel(excel_file, index=False)

        response = send_file(excel_file, as_attachment=True)

        os.remove(excel_file)

        return response
        
    return render_template('download.html', form=form)

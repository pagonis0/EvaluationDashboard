import os
import json
import random
import psutil
import traceback

from flask import Flask, render_template, request, session, redirect, Blueprint
from flask_session import Session
from werkzeug.exceptions import abort
from requests.exceptions import HTTPError
from datetime import datetime
from jinja2 import Template
# from bs4 import BeautifulSoup as Soup

from RecommendationSystem.api import MoodleAPI, RecommenderAPI
from RecommendationSystem.dash_layout import init_dash, dash_layout, dynamic_layout, difference
from FlaskDash import dash

"""
The routes for the Flask component working with the test recommendation interface.
"""

interface = Blueprint('interface', __name__)



moodle = MoodleAPI()
recommender = RecommenderAPI()
lns_json, lns_table, cmid2lnid, course_table = moodle._get_lns()
random.seed(a=42)

print(">>> loaded:", psutil.Process(os.getpid()).memory_info().rss / 1024)


# ============ routes ============
@interface.route("/interface")
def index():
    if not session.get("id"):
        return redirect('/eval/interface/init_session')
    print(">> session_id:", session.get('id'))

    print(">>> index:", psutil.Process(os.getpid()).memory_info().rss / 1024)
    print(">> origin:", request.environ)
    return render_template("index.html",
                           has_recommendation=(len(session.get('recommendations')[-1]) > 0))


@interface.route('/interface/<int:ln_id>')
def ln(ln_id):
    if not session.get("id"):
        return redirect('/eval/interface/init_session')

    ln = MoodleAPI()._get_post(ln_id)
    print(">>> ln:", psutil.Process(os.getpid()).memory_info().rss / 1024)
    return render_template('ln.html',
                           ln=ln, has_recommendation=(len(session.get('recommendations')[-1]) > 0))


@interface.route('/interface/lns', methods=('GET', 'POST'))
def lns():
    if not session.get("id"):
        return redirect('/eval/interface/init_session')
    current_history = session.get('current_history')

    if request.method == 'POST':
        if ('update_button' in request.form and
                request.form['update_button'] == 'update'):
            global lns_json
            global lns_table
            global course_table
            global cmid2lnid
            lns_json, lns_table, cmid2lnid, course_table = MoodleAPI()._get_lns(update=True)
            return redirect("/lns")

        if 'add_button' in request.form:
            # global current_history
            print("add", request.form['add_button'])
            current_history.append([request.form['add_button'], 0.5])
            # print(current_history)
            session['current_history'] = current_history
        print(">>> lns add_button:", psutil.Process(os.getpid()).memory_info().rss / 1024)
        return "", 204

    print(">>> lns:", psutil.Process(os.getpid()).memory_info().rss / 1024)
    return render_template('lns.html',  # session_id=session_id,
                           title='Learning Nuggets', column_names=lns_table[0],
                           row_data=lns_table[1:], zip=zip, enumerate=enumerate,
                           has_recommendation=(len(session.get('recommendations')[-1]) > 0))


@interface.route('/interface/courses', methods=('GET', 'POST'))
def courses():
    if not session.get("id"):
        return redirect('/eval/interface/init_session')
    enrolled = session.get('enrolled')

    if request.method == 'POST':
        if ('update_button' in request.form and
                request.form['update_button'] == 'update'):
            global lns_json
            global lns_table
            global course_table
            global cmid2lnid
            lns_json, lns_table, cmid2lnid, course_table = MoodleAPI()._get_lns(update=True)
            return redirect("/lns")

        if ('add_button' in request.form and
                request.form['add_button'] != 0):
            
            if (None, "") in enrolled:
                enrolled.remove((None, ""))

            print("add", request.form['add_button'])
            entry = (request.form['add_button'], request.form['name'])
            if entry not in enrolled:
                enrolled.append(entry)
            # print(enrolled)
            session['enrolled'] = enrolled
        print(">>> courses add_button:", psutil.Process(os.getpid()).memory_info().rss / 1024)
        return "", 204

    print(">>> courses:", psutil.Process(os.getpid()).memory_info().rss / 1024)
    return render_template('courses.html',
                           title='Courses', column_names=course_table[0],
                           row_data=course_table[1:], zip=zip, enumerate=enumerate,
                           has_recommendation=(len(session.get('recommendations')[-1]) > 0))


@interface.route('/interface/profile', methods=('GET', 'POST'))
def profile():
    if not session.get("id"):
        return redirect('/eval/interface/init_session')

    global lns_json

    if request.method == 'POST':
        print(request.form)

        if 'remove_ln_button' in request.form:
            to_remove = int(request.form['remove_ln_button'])
            print(request.form['remove_ln_button'])
            print(session['current_history'][int(request.form['remove_ln_button'])])
            current_history = session.get('current_history')
            del current_history[to_remove]
            session['current_history'] = current_history

        if 'remove_course_button' in request.form:
            to_remove = int(request.form['remove_course_button'])
            print(request.form['remove_course_button'])
            print(session['enrolled'][int(request.form['remove_course_button'])])
            enrolled = session.get('enrolled')
            del enrolled[to_remove]
            session['enrolled'] = enrolled

        if 'grade_button' in request.form:
            current_history = session.get('current_history')
            current_history[int(request.form['index'])][1] = request.form['grade']
            session['current_history'] = current_history

        if 'options' in request.form:
            session['learning_style'] = request.form["options"]

        if 'recommend_button' in request.form:
            print(session['enrolled'])
            _recommend()
            return redirect("/eval/interface/recommendation")

    current_history = session.get('current_history')
    enrolled = session.get('enrolled')
    lns = []
    for ln_id, grade in current_history:
        entry = lns_json[int(ln_id)]
        entry["ln_id"] = int(ln_id)
        entry["grade"] = float(grade)
        lns.append(entry)

    enrolled_json = [{"ID": entry[0], "name": entry[1]} for entry in enrolled]
    print(">>> profile:", psutil.Process(os.getpid()).memory_info().rss / 1024)
    return render_template("profile.html",
                           lns=lns, courses=enrolled_json, zip=zip, len=len, enumerate=enumerate,
                           ln_indices=list(range(len(lns))), course_indices=list(range(len(enrolled))),
                           learning_style=session.get('learning_style'),
                           has_recommendation=(len(session.get('recommendations')[-1]) > 0))


def _recommend():

    query = {
        "query": "concept_path",
        "target": {
            "target_id": "all",
            "target_type": "course",
            "threshold": 0.6
        },
        "learning_style": {
            "Diverging": 0,
            "Assimilating": 0,
            "Converging": 0,
            "Accomodating": 0
        },
        "courses": [
            int(course[0]) for course in session.get('enrolled')
        ],
        "history": {
            "course_placeholder": {
                str(i): {"ln_id": int(entry[0]),
                         "grade": float(entry[1]),
                         "section_id": lns_json[int(entry[0])]["section_id"],
                         "grade_date_modified": i}
                for i, entry in enumerate(session.get('current_history'))
            }
        }
    }
    query["learning_style"][session.get('learning_style')] = 1

    # print(query)
    try:
        if session.get("recommendations")[-1] == {}:
            session['recommendations'][0] = recommender.get_recommendation(query)
        else:
            session['recommendations'].append(recommender.get_recommendation(query))
        if len(session.get('current_history')) > 0:
            last_entry = session.get('current_history')[-1]
            record = {"id": int(last_entry[0]),
                      "grade": float(last_entry[1]),
                      "section": f"S_{lns_json[int(last_entry[0])]['section_id']}",
                      "name": lns_json[int(last_entry[0])]["ln_name"]}
            session['record'].append(record)
        else:
            record = {"id": 0, "name": f"<start>", "grade": 0, "section": ""}
            session['record'].append(record)
    except HTTPError as e:
        print(e)
        print(traceback.format_exc())

    with open("tmp_rec.json", "w") as jfile:
        json.dump(session.get('recommendations'), jfile, indent=2)
    # print(session.get('recommendations')[-1])


@interface.route('/interface/recommendation', methods=('GET', 'POST'))
def recommend():
    if not session.get("id"):
        return redirect('/eval/interface/init_session')

    global lns_json
    global cmid2lnid

    current_history = session.get('current_history')
    recommendation = session.get('recommendations')[-1]

    if request.method == 'POST':
        if 'add_ln_button' in request.form:
            print("add", request.form['add_ln_button'])
            current_history.append([request.form['add_ln_button'], 0.5])
            session['current_history'] = current_history
            return "", 204
        elif 'recommend_button' in request.form:
            _recommend()
            print('reload')
        elif 'show_steps' in request.form:
            n_steps = len(session.get('record'))
            #session['dash'] = dash_layout(session.get("id"), n_steps,
            #                              session.get('record'),
            #                              session.get('recommendations'))
            session['diff'] = difference(n_steps=len(session.get('record')), 
                                         paths=session.get('recommendations'),
                                         records=session.get('record'),
                                         course=session.get('enrolled')[0][0])
            # dash.layout = dynamic_layout(session) # session.get('dash')
            dash.layout = session.get('dash')
            # return redirect('/steps')
            return redirect('/eval/interface/testathing')

    # print(cmid2lnid)
    print(json.dumps(recommendation, indent=2))
    print(">>> recommend:", psutil.Process(os.getpid()).memory_info().rss / 1024)
    for course in recommendation["courses"]:
        for sec in course["section_path"]:
            for ln in sec["learning_nuggets"]:
                print(f"{course['course']['id']} : {course['course']['name']} |"
                      f" {sec['resp_id']} : {sec['name']} |"
                      f" {ln['id']}")
                cmid = ln["id"]
                lnid = cmid2lnid[cmid]
                ln_info = lns_json[lnid]
                ln_name = ln_info["ln_name"]
    return render_template("recommendation.html",
                           has_recommendation=(len(recommendation) > 0),
                           recommendation=recommendation, lns=lns_json, cmid2lnid=cmid2lnid,
                           enumerate=enumerate)


@interface.route('/interface/testathing', methods=('GET', 'POST'))
def testathing():

    max_steps = len(session.get('record'))
    n_steps = max_steps
    course = session.get('enrolled')[0][0]
    print(" >> TESTATHING:", course)

    if request.method == "POST":
        if "steps" in request.form:
            n_steps = request.form["steps"]
        if "course" in request.form:
            course = request.form["course"]
            print(" >> TESTATHING - POST:", course)
        session["diff"] = difference(n_steps=n_steps, 
                                     paths=session.get('recommendations'),
                                     records=session.get('record'),
                                     course=course)
    
    fig_data = {"fig":session.get('diff').to_html(full_html=False)}
    template = render_template("testathing.html", fig="{{ fig }}", 
                               max_steps=max_steps, n_steps=n_steps, 
                               courses=session.get('enrolled'))
    html = Template(template)
    return html.render(fig_data)


@interface.route('/interface/init_session')
def init_session():
    date = datetime.now()
    session_id = date.strftime('%d.%m.%Y-%H:%M:%S.%f')+"-"+str(random.random())[2:5]
    print(date)
    print(session_id)

    session['id'] = session_id
    session['current_history'] = []
    session['enrolled'] = []
    session['learning_style'] = "Diverging"
    session['recommendations'] = [{}]
    session['record'] = []
    session['diff'] = difference(None, None, None, None)
    session['dash'] = dash_layout(session_id, 0, records=[], paths=[], init=True)
    # dash.layout = dynamic_layout(session)
    return redirect('/eval/interface')


@interface.route('/interface/reset_session')
def reset_session():

    session.pop("id", None)
    return redirect('/eval/interface/init_session')


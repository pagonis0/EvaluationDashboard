from flask import render_template, Blueprint
import requests, json, os
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

"""
The routes for the Flask component working with the dash application part.
Mostly dash pages are integrated as an iframe.
"""

dash = Blueprint('dash', __name__)

@dash.route("/dash/nutzung")
def nutzung():
    return render_template("nutzung.html")

@dash.route("/dash/noten")
def noten():
    return render_template("working.html")

@dash.route("/dash/static/primussws23")
def primussws23():
    base_path = '/app/StaticDashboard/primuss_ws23_plots'
    with open(os.path.join(base_path, 'plot1.json')) as f:
        fig1 = json.load(f)
    with open(os.path.join(base_path, 'plot2.json')) as f:
        fig2 = json.load(f)
    with open(os.path.join(base_path, 'plot3.json')) as f:
        fig3 = json.load(f)
    with open(os.path.join(base_path, 'plot4.json')) as f:
        fig4 = json.load(f)
    with open(os.path.join(base_path, 'plot5.json')) as f:
        fig5 = json.load(f)
    with open(os.path.join(base_path, 'plot6.json')) as f:
        fig6 = json.load(f)
    with open(os.path.join(base_path, 'plot7.json')) as f:
        fig7 = json.load(f)
    with open(os.path.join(base_path, 'plot8.json')) as f:
        fig8 = json.load(f)
    with open(os.path.join(base_path, 'plot9.json')) as f:
        fig9 = json.load(f)
    with open(os.path.join(base_path, 'plot10.json')) as f:
        fig10 = json.load(f)
    with open(os.path.join(base_path, 'plot11.json')) as f:
        fig11 = json.load(f)
    with open(os.path.join(base_path, 'plot12.json')) as f:
        fig12 = json.load(f)
    
    return render_template('primussws23.html', plot1=fig1, plot2=fig2, plot3=fig3, plot4=fig4,
                           plot5=fig5, plot6=fig6, plot7=fig7, plot8=fig8, plot9=fig9, plot10=fig10, plot11=fig11, plot12=fig12)


@dash.route("/dash/chatbot")
def chatbot_overview():
    return render_template("chatbot.html")
    #return render_template("working.html")

from flask import Flask
from usage_dash import create_usage_board
#from score_dash import create_score_board

app = Flask(__name__, static_url_path='/flaskdash/static')
app.config['SECRET_KEY'] = '061f21bcd3a44531574c97c17b75da45'
create_usage_board(app)
#create_score_board(app)


from flaskdash import routes

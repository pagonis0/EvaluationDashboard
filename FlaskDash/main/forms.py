from flask_wtf import FlaskForm
from wtforms import SelectField
from wtforms.validators import DataRequired

class DownloadForm(FlaskForm):
    academic_year = SelectField('Studienjahr', validators=[DataRequired()], choices=[])
    semester = SelectField('Semester', validators=[DataRequired()], choices=[])
    course = SelectField('Kurs', validators=[DataRequired()], choices=[])   

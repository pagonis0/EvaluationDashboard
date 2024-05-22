from flask_wtf import FlaskForm
from wtforms import SelectField, BooleanField
from wtforms.validators import DataRequired

class DownloadForm(FlaskForm):
    #name = SelectField('Name', validators=[DataRequired()], choices=[])
    academic_year = SelectField('Studienjahr', validators=[DataRequired()], choices=[])
    semester = SelectField('Semester', validators=[DataRequired()], choices=[])
    course = SelectField('Kurs', validators=[DataRequired()], choices=[])   

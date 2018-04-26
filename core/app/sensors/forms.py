from flask_wtf import Form
from wtforms import SubmitField

class EditInfluxDBForm(Form):
    reset = SubmitField()
    delete = SubmitField()

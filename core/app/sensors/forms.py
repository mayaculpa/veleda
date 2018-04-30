from flask_wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import Length, Regexp


class EditInfluxDBForm(Form):
    reset = SubmitField()
    delete = SubmitField()


class NewInfluxDBForm(Form):
    name = StringField('Database name', validators=[Length(min=1, max=64, message="Name must be between 1 and 64 characters"),
                                                    Regexp('^[a-zA-Z0-9_-]*$', message="Name may only contain letters, numbers, '-' and '_'")])
    submit = SubmitField('Create')

class UpdateInfluxDBAccessForm(Form):
    update = SubmitField('Reset Access Key')

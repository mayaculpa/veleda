from flask_wtf import Form
from wtforms import SubmitField

from ..models import Client

class ConfirmForm(Form):
    confirm = SubmitField()
    cancel = SubmitField()

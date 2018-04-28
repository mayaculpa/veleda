from flask import Blueprint

sensors = Blueprint('sensors', __name__)

from . import views # noqa
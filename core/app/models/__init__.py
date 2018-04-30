"""
These imports enable us to make all defined models members of the models
module (as opposed to just their python files)
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# from . import user, miscellaneous, oauth, sensors
from .user import *  # noqa
from .miscellaneous import *  # noqa
from .oauth import * # noqa
from .sensors import * # noqa

def init_app(app):
    db.init_app(app)
    sensors.init_app(app)

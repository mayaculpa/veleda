from flask import render_template
from flask_login import login_required, current_user

from . import sensors
from ..models import InfluxDB

@sensors.route('/')
@login_required
def index():
    return render_template('sensors/index.html', influx_dbs=current_user.influx_dbs)

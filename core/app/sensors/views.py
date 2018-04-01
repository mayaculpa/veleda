from flask import render_template
from flask_login import login_required

from . import sensors

@sensors.route('/')
@login_required
def index():
    return render_template('sensors/index.html')
from flask import render_template

from . import sensors

@sensors.route('/')
def index():
    return render_template('sensors/index.html')
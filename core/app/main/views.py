from flask import render_template, redirect
from ..models import EditableHTML

from . import main


@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    return redirect('https://veleda.io')

@main.route('/data')
def data():
    return redirect('https://data.veleda.io')
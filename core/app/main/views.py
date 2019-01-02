from flask import render_template, redirect

from . import main


@main.route('/')
def index():
    return render_template('main/index.html')


@main.route('/about')
def about():
    return redirect('https://flowleaf.co')

@main.route('/data')
def data():
    return redirect('https://data.flowleaf.co')

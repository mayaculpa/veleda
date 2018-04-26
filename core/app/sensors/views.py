from flask import render_template, flash
from flask_login import login_required, current_user

from . import sensors
from .forms import EditInfluxDBForm
from ..models import InfluxDB
from .. import influx_db_client

@sensors.route('/influx_db')
@login_required
def index():
    """List Influx databases"""
    return render_template('sensors/index.html', influx_dbs=current_user.influx_dbs)

@sensors.route('/influx_db/<int:influx_db_id>', methods=['GET', 'POST'])
@login_required
def edit_influx_db(influx_db_id):
    """Modify Influx databases"""
    influx_db=InfluxDB.query.get(influx_db_id)
    form=EditInfluxDBForm()
    if form.validate_on_submit():
        # Check which button was pressed
        if form.reset.data:
            influx_db_client.drop_database(influx_db.name)
            influx_db_client.create_database(influx_db.name)
            influx_db_client.grant_privilege('all', influx_db.name, influx_db.owner)
            flash('Database {} successfully reset'.format(influx_db.name),
                  'form-success')
        if form.delete.data:
            influx_db_client.drop_database(influx_db.name)
            flash('Database {} successfully deleted'.format(influx_db.name),
                  'form-success')
    return render_template('sensors/index.html',
                           form=form,
                           influx_db=influx_db)

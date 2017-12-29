#################
#### imports ####
#################

from flask import render_template, Blueprint, request, redirect, url_for, flash, abort
from sqlalchemy.exc import IntegrityError
from flask_login import login_user, current_user, login_required, logout_user
from flask_mail import Message
from threading import Thread
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime

from .forms import RegisterForm, LoginForm, EmailForm, PasswordForm
from thymedata import db, mail, app
from thymedata.models import User


################
#### config ####
################

users_blueprint = Blueprint('users', __name__)


##########################
#### helper functions ####
##########################



################
#### routes ####
################

@users_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                new_user = User(form.email.data, form.password.data)
                new_user.authenticated = True
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                send_confirmation_email(new_user.email)
                flash('Thanks for registering!  Please check your email to confirm your email address.', 'success')
                return redirect(url_for('recipes.user_recipes', recipe_type='All'))
            except IntegrityError:
                db.session.rollback()
                flash('ERROR! Email ({}) already exists.'.format(form.email.data), 'error')
    return render_template('register.html', form=form)


@users_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user is not None and user.is_correct_password(form.password.data):
                user.authenticated = True
                user.last_logged_in = user.current_logged_in
                user.current_logged_in = datetime.now()
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash('Thanks for logging in, {}'.format(current_user.email))
                return redirect(url_for('index'))
            else:
                flash('ERROR! Incorrect login credentials.', 'error')
    return render_template('login.html', form=form)

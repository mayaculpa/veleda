import os
from flask import Flask
from flask_assets import Environment

from config import config
from .assets import app_css, app_js, vendor_css, vendor_js

basedir = os.path.abspath(os.path.dirname(__file__))


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    # not using sqlalchemy event system, hence disabling it
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    config[config_name].init_app(app)
    models.init_app(app)
    services.init_app(app)

    # Register Jinja template functions
    from .utils import register_template_utils
    register_template_utils(app)

    # Set up and build asset pipeline
    assets_env = Environment(app)
    dirs = ['assets/styles', 'assets/scripts']
    for path in dirs:
        assets_env.append_path(os.path.join(basedir, path))
    assets_env.url_expire = True

    assets_env.register('app_css', app_css)
    assets_env.register('app_js', app_js)
    assets_env.register('vendor_css', vendor_css)
    assets_env.register('vendor_js', vendor_js)

    app_css.build()
    app_js.build()
    vendor_css.build()
    vendor_js.build()

    # Configure SSL if platform supports it
    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask.ext.sslify import SSLify
        SSLify(app)

    # Create app blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .account import account as account_blueprint
    app.register_blueprint(account_blueprint, url_prefix='/account')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .oauth import oauth as oauth_blueprint
    app.register_blueprint(oauth_blueprint, url_prefix='/oauth')

    from .sensors import sensors as sensors_blueprint
    app.register_blueprint(sensors_blueprint, url_prefix='/sensors')

    return app

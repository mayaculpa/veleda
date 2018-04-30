from flask_compress import Compress
from flask_login import LoginManager
from flask_oauthlib.provider import OAuth2Provider
from flask_rq2 import RQ
from flask_wtf import CsrfProtect

from .email import *

compress = Compress()
login_manager = LoginManager()
oauth_provider = OAuth2Provider()
rq = RQ()
csrf = CsrfProtect()

def init_app(app):
    """Set up extensions"""
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'account.login'
    login_manager.init_app(app)
    csrf.init_app(app)
    compress.init_app(app)
    oauth_provider.init_app(app)
    rq.init_app(app)

    mail.init_app(app)

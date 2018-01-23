import base64
import unittest
from datetime import datetime, timedelta

from faker import Faker
from flask import url_for

from app import create_app, db
from app.models import Client, Grant, Token, Permission, Role, User


def to_unicode(text):
    if not isinstance(text, str):
        text = text.decode('utf-8')
    return text

def to_bytes(text):
    if isinstance(text, str):
        text = text.encode('utf-8')
    return text

def to_base64(text):
    return to_unicode(base64.b64encode(to_bytes(text)))

class OauthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.prepare_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

###############
### Helpers ###
###############

    def prepare_data(self):
        general_role = Role(name="User", index="main", permissions=Permission.GENERAL)
        db.session.add(general_role)
        db.session.commit()
        
        User.generate_fake(1)
        
        oauth_client = Client(
            name='ios',
            client_id='code-client',
            client_secret='code-secret',
            _redirect_uris='http://localhost/oauth/authorized',
            _default_scopes='email'
        )
        db.session.add(oauth_client)
        db.session.commit()

        self.oauth_client = oauth_client
        self.authorize_url = (
            url_for('oauth.authorize') + '?response_type=code&client_id=%s'
        ) % oauth_client.client_id

    def login(self, email, password):
        self.client.get('/login', follow_redirects=True)
        return self.client.post(
            url_for('account.login'),
            data=dict(email=email, password=password),
            follow_redirects=True
        )

    def login_default(self):
        self.user = User.query.first()
        return self.login(self.user.email, 'password')

#############
### Tests ###
#############

    def test_login(self):
        """Test the login helper functions."""
        rv = self.login_default()
        self.assertIn(str.encode(self.user.first_name), rv.data)
        self.assertIn(str.encode(self.user.last_name), rv.data)

    def test_integration_get_authorize_without_login(self):
        """Should redirect to login page as not logged in."""
        response = self.client.get(url_for('oauth.authorize'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(b'You should be redirected automatically to target URL:',
                      response.data)
        self.assertIn(str.encode(url_for('account.login')), response.data)

    def test_get_authorize_errors(self):
        """Should return error messages."""
        self.login_default()
        rv = self.client.get(url_for('oauth.authorize'))
        assert 'client_id' in rv.location
        
        rv = self.client.get(url_for('oauth.authorize') + '?client_id=no')
        assert 'client_id' in rv.location

        url = (
            url_for('oauth.authorize')
            + '?client_id=%s'
            % self.oauth_client.client_id
        )
        rv = self.client.get(url)
        assert 'error' in rv.location

    def test_get_authorize_successfully(self):
        """Should return confirmation page."""
        self.login_default()
        rv = self.client.get(self.authorize_url)
        assert b'confirm' in rv.data

    def test_get_invalid_scope(self):
        """Should return invalid scope error."""
        self.login_default()
        url = self.authorize_url + '&scope=foo'
        rv = self.client.post(url, data={'confirm': True})
        assert 'invalid_scope' in rv.location

    def test_post_authorize(self):
        """Should return invalid scope error."""
        self.login_default()
        url = self.authorize_url + '&scope=email'
        rv = self.client.post(url, data={'confirm': True})
        assert 'code' in rv.location

    def test_missing_scope(self):
        """Should return invalid scope error."""
        self.login_default()
        url = self.authorize_url + '&scope='
        rv = self.client.post(url, data={'confirm': True})
        assert 'error=Scopes+must+be+set' in rv.location

    def test_confirm_authorize_request(self):
        """Should accept authorization request."""
        self.login_default()
        url = self.authorize_url + '&scope=email'
        rv = self.client.post(url, data={'confirm': True})
        assert 'code=' in rv.location

    def test_cancel_authorize_request(self):
        """Should accept authorization request."""
        self.login_default()
        url = self.authorize_url + '&scope=email'
        rv = self.client.post(url, data={'cancel': True})
        assert 'access_denied' in rv.location

    def test_invalid_redirect_uri(self):
        self.login_default()
        url = (
            self.authorize_url +
            '&redirect_uri=http://localhost:8000/unknown_url'
            '&scope=email'
        )
        rv = self.client.get(url)
        assert 'error=' in rv.location
        assert 'Mismatching+redirect+URI' in rv.location

    def test_invalid_token(self):
        rv = self.client.post(url_for('oauth.access_token'))
        assert b'unsupported_grant_type' in rv.data

        rv = self.client.post('/oauth/token?grant_type=authorization_code')
        assert b'error' in rv.data
        assert b'code' in rv.data

        url = (
            '/oauth/token?grant_type=authorization_code'
            '&code=nothing&client_id=%s'
        ) % self.oauth_client.client_id
        rv = self.client.post(url)
        assert b'invalid_client' in rv.data

        url += '&client_secret=' + self.oauth_client.client_secret
        rv = self.client.post(url)
        assert b'invalid_client' not in rv.data
        assert rv.status_code == 401

    def test_get_token(self):
        expires = datetime.utcnow() + timedelta(seconds=100)
        grant = Grant(
            user_id=1,
            client_id=self.oauth_client.client_id,
            _scopes=self.oauth_client._default_scopes,
            redirect_uri='http://localhost/oauth/authorized',
            code='test-get-token',
            expires=expires
        )
        db.session.add(grant)
        db.session.commit()

        url = (
            '/oauth/token?grant_type=authorization_code&code=test-get-token'
            '&redirect_uri=http://localhost/oauth/authorized'
        )
        rv = self.client.post(
            url + '&client_id=%s' % (self.oauth_client.client_id)
        )
        assert b'invalid_client' in rv.data

        rv = self.client.post(
            url + '&client_id=%s&client_secret=%s' % (
                self.oauth_client.client_id,
                self.oauth_client.client_secret
            )
        )
        assert b'access_token' in rv.data

        # Prvious grant was deleted by last successful authentication
        assert Grant.query.count() == 0

        grant = Grant(
            user_id=1,
            client_id=self.oauth_client.client_id,
            _scopes=self.oauth_client._default_scopes,
            redirect_uri='http://localhost/oauth/authorized',
            code='test-get-token',
            expires=expires
        )
        db.session.add(grant)
        db.session.commit()

        rv = self.client.post(url, headers={
            'authorization': 'Basic ' + to_base64(
                '%s:%s' % (
                    self.oauth_client.client_id,
                    self.oauth_client.client_secret
                )
            )
        })
        assert b'access_token' in rv.data

    def test_deny_user_info(self):
        url = '/oauth/api/userinfo'
        rv = self.client.get(url, follow_redirects=True)
        assert rv.status_code == 401
        assert b'Unauthorized' in rv.data

    def test_allow_user_info(self):
        url = '/oauth/api/userinfo'
        expires = datetime.utcnow() + timedelta(seconds=100)

        token = Token(
            client_id='a_client_id',
            user_id=User.query.first().id,
            token_type='bearer',
            access_token='an_access_token',
            refresh_token='a_refresh_token',
            expires=expires,
            _scopes='email'
        )
        db.session.add(token)
        db.session.commit()

        rv = self.client.get(url, headers={
            'authorization': 'Bearer ' + token.access_token
        })
        assert rv.status_code == 200
        assert b'email' in rv.data
        assert b'sub' in rv.data

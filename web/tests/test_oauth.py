import unittest
from flask import url_for
from faker import Faker

from app import create_app, db
from app.models import Client, User, Role, Permission

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
        admin_role = Role(name="Administrator", index="admin", permissions=Permission.ADMINISTER)
        general_role = Role(name="User", index="main", permissions=Permission.GENERAL)
        db.session.add(admin_role)
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

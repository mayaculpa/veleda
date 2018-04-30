import unittest
import fakeredis

from flask import url_for

from app import create_app
from app.models import db, Permission, Role, User

class UserViewTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.prepare_data()
        self.r = fakeredis.FakeStrictRedis()

    def tearDown(self):
        self.r.flushall()
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

        user = User(email='test@example.com',
                    password='password',
                    confirmed=True,
                    first_name='hello',
                    last_name='world',
                    role=general_role)
        db.session.add(user)
        db.session.commit()

    def login(self, username, password):
        return self.client.post(url_for('account.login'), data=dict(
            email=username,
            password=password
            ), follow_redirects=True)

    def test_valid_login(self):
        user = User.query.first()
        rv = self.login(user.email, 'password')
        self.assertIn(str.encode(user.first_name), rv.data)
        self.assertIn(str.encode(user.last_name), rv.data)

    def test_invalid_login(self):
        user = User.query.first()
        rv = self.login(user.email, 'notpassword')
        self.assertIn(str.encode('Invalid email or password'), rv.data)

    def test_get_registration(self):
        rv = self.client.get(url_for('account.register'))
        self.assertIn(str.encode('Create an account'), rv.data)

    def test_create_registration(self):
        rv = self.client.post(url_for('account.register'),
                data=dict(
                    first_name='first',
                    last_name='last',
                    email='hi@example.com',
                    password='password2',
                    password2='password2'
                ), follow_redirects=True)
        self.assertIn(str.encode('A confirmation link has been sent to hi@example.com'),
                      rv.data)

import os
import unittest

from thymedata import app, db, mail


TEST_DB = 'test.db'


class BasicTests(unittest.TestCase):

    ############################
    #### setup and teardown ####
    ############################

    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join(app.config['BASEDIR'], TEST_DB)
        app.config['SQLALCHEMY_ECHO'] = False
        self.app = app.test_client()
        db.drop_all()
        db.create_all()

        mail.init_app(app)
        self.assertEqual(app.debug, False)

    # executed after each test
    def tearDown(self):
        pass


    ########################
    #### helper methods ####
    ########################

    def register(self, email, password, confirm):
        return self.app.post(
            '/register',
            data=dict(email=email, password=password, confirm=confirm),
            follow_redirects=True)


    ###############
    #### Tests ####
    ###############

    def test_main_page(self):
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_valid_user_registration(self):
        response = self.register('user@example.com',
                                 'Password$1',
                                 'Password$1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thanks for registering!', response.data)

    def test_invalid_user_registration_different_passwords(self):
        response = self.register('user@example.com',
                                 'Password$1',
                                 'Password$2')
        self.assertIn(b'Field must be equal to password.', response.data)

    def test_invalid_user_registration_duplicate_email(self):
        response = self.register('user@example.com',
                                 'Password$1',
                                 'Password$1')
        self.assertEqual(response.status_code, 200)
        response = self.register('user@example.com',
                                 'Password$3',
                                 'Password$3')
        self.assertIn(b'ERROR! Email (user@example.com) already exists.', response.data)


if __name__ == "__main__":
    unittest.main()

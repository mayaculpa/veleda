import unittest

from app import create_app, db
from app.models import InfluxDB, Role, User

class InfluxDBModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_sensor_user_relationship(self):
        Role.insert_roles()
        User.generate_fake(count=1)
        user = User.query.first()

        influxDB = InfluxDB(name='first_db', owner_id=user.id)
        db.session.add(influxDB)
        db.session.commit()

        self.assertIsNotNone(user)
        self.assertEqual(influxDB.owner, user)

import random
import string

from influxdb import InfluxDBClient

from . import db

influx_db_client = InfluxDBClient()

def init_app(app):
    # Connect to InfluxDB
    influx_db_client.close()
    influx_db_client.__init__(
        host=app.config['INFLUXDB_HOST'],
        username=app.config['INFLUXDB_ADMIN_USER'],
        password=app.config['INFLUXDB_ADMIN_PASSWORD'])

class InfluxDB(db.Model):
    __tablename__ = 'influx_dbs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', back_populates='influx_dbs')
    missing_owner = db.Column(db.Boolean, default=False)

    def create_database(self):
        """Create an InfluxDB"""
        influx_db_client.create_database(self.name)
        self.check_and_create_valid_owner()
        influx_db_client.grant_privilege('all', self.name, str(self.owner_id))
        db.session.add(self)
        db.session.commit()

    def drop_database(self):
        """Drop the influx database"""
        influx_db_client.drop_database(self.name)
        db.session.delete(self)
        db.session.commit()

    def reset_database(self):
        """Reset the influx database"""
        influx_db_client.drop_database(self.name)
        influx_db_client.create_database(self.name)

        self.check_and_create_valid_owner()
        influx_db_client.grant_privilege('all', self.name, str(self.owner_id))

    def check_and_create_valid_owner(self):
        """Checks and fixes owner information. Returns true on success"""
        if(self.owner is None):
            self.missing_owner = True
            db.session.add(self)
            db.session.commit()
            return False
        if(self.owner.influx_db_access_key is None):
            access_key = ''.join(random.SystemRandom().choice(
                string.ascii_uppercase + string.digits) for _ in range(20))
            influx_db_client.set_user_password(str(self.owner_id), access_key)
            self.owner.influx_db_access_key = access_key
            db.session.add(self.owner)
            db.session.commit()
        return True

from .. import db

class InfluxDB(db.Model):
    __tablename__ = 'influx_dbs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', back_populates='influx_dbs')

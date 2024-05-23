from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class AirplaneStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pilot = db.Column(db.String(50), nullable=False)
    copilot = db.Column(db.String(50), nullable=False)
    departure_hour = db.Column(db.Time, nullable=False)
    arrival_hour = db.Column(db.Time, nullable=False)
    total_flown_hours = db.Column(db.Float, nullable=False)
    departure_place = db.Column(db.String(100), nullable=False)
    flight_type = db.Column(db.String(50), nullable=False)
    observation = db.Column(db.String(200), nullable=False)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)

class Aircraft(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    statuses = db.relationship('AirplaneStatus', backref='aircraft', lazy=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    
    

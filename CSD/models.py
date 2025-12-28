from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # يتولد تلقائيًا
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)       # "admin" or "user"
    user_type = db.Column(db.String(50), nullable=False)  # e.g., "admin", "student"
    location = db.Column(db.String(120), default="")      # optional "lat,long"

    # علاقة مع المواقع - Cascade delete
    locations = db.relationship(
        "UserLocation",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )


class SensorData(db.Model):
    __tablename__ = "sensor_data"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # يتولد تلقائيًا
    sensor_id = db.Column(db.String(120), unique=True, nullable=False)
    sensor_type = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)  # "lat,long"
    value = db.Column(db.String(120), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)


class UserLocation(db.Model):
    __tablename__ = "user_locations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # يتولد تلقائيًا
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )  # ربط مع جدول User
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
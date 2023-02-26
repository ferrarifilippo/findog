from _datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

'''class ModelTableName(db.Model):
    #table column unique id with a primary key
    data_column_uniqueid = db.Column(db.Integer, primary_key = True)
    
    #table column field with data type
    data_column_field = db.Column(db.ColumnDataType, nullable = False)'''


class DogOwner(db.Model):
    __tablename__ = 'dog_owner'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    email = db.Column(db.String)
    address = db.Column(db.String)
    phone = db.Column(db.String)
    password = db.Column(db.String)
    dog = db.relationship('Dog', backref='owner', uselist=True, lazy='dynamic')
    authenticated = db.Column(db.Boolean, default=False)
    telegram_chat_id = db.Column(db.String)

    def name(self):
        """True, as all users are active."""
        return self.first_name

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.id

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False


class Dog(db.Model):
    __tablename__ = 'dog'
    uuid = db.Column(db.String, primary_key=True, autoincrement=False)
    name = db.Column(db.String)
    breed = db.Column(db.String)
    color = db.Column(db.String)
    user = db.Column(db.Integer, db.ForeignKey('dog_owner.id'),nullable=False)
    state = db.Column(db.String)
    created_at = db.Column(db.DateTime(timezone=True),nullable=False, server_default=func.now())
    bridge_paired = db.Column(db.String, default="False")
    walk = db.relationship('Walk', backref='walk', uselist=True, lazy='dynamic')
    habits = db.relationship('Habits', backref='habits', uselist=False, lazy=True)


class Walk(db.Model):
    __tablename__='walk'
    id = db.Column(db.Integer, primary_key=True)
    dog = db.Column(db.String, db.ForeignKey('dog.uuid'), nullable=False)
    time = db.Column(db.DateTime(timezone=True))
    day_slot = db.Column(db.String)

class Habits (db.Model):
    __tablename__='habits'
    id = db.Column(db.Integer, primary_key=True)
    dog = db.Column(db.String, db.ForeignKey('dog.uuid'), nullable=False)
    morning = db.Column(db.Time(timezone=True))
    afternoon = db.Column(db.Time(timezone=True))
    evening = db.Column(db.Time(timezone=True))


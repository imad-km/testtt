
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import string
import random

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstnameen = db.Column(db.Text(), nullable=False)
    lastnameen = db.Column(db.Text(), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    city = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    role = db.Column(db.Text(), nullable=False)
    n_token = db.Column(db.Text(), nullable=False)
    identify = db.Column(db.Text(), nullable=False)
    def __repr__(self) -> str:
        return f'User>>> {self.firstnameen}'

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    date_birthday = db.Column(db.String(50), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    email = db.Column(db.Text(), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    price = db.Column(db.Text(), nullable=False)
    image = db.Column(db.Text(), nullable=False)
    time_start = db.Column(db.String(200), nullable=False)
    time_end = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(200), nullable=False)
    adress = db.Column(db.Text(), nullable=False)
    localisation = db.Column(db.Text(), nullable=False)
    image_clinik = db.Column(db.Text(), nullable=False)
    description = db.Column(db.Text(), nullable=False)
    weak = db.Column(db.String(200), nullable=False)
    rate = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="waiting", nullable=False)
    role = db.Column(db.Text(), nullable=False)
    ticket = db.Column(db.Text(), nullable=False)
    identify = db.Column(db.Text(), nullable=False)
    def __repr__(self):
        return f'Doctor>>> {self.firstname} {self.lastname}'

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstnameen = db.Column(db.String(80), unique=True, nullable=False)
    lastnameen = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    role = db.Column(db.Text(), nullable=False)
    identify = db.Column(db.Text(), nullable=False)

    def __repr__(self) -> str:
        return f'Admin>>> {self.firstnameen}'

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text(), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    identify = db.Column(db.Text(), nullable=False)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Text(), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    ticket_number = db.Column(db.Integer, nullable=False, default=1)
    ticket_code = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())
    fullname = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Text(), nullable=False)
    n_token = db.Column(db.Text(), nullable=False)
    doctor = db.relationship('Doctor', back_populates='tickets')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Auto-set on creation
    expiry_date = db.Column(db.DateTime, nullable=False)
    skip = db.Column(db.Text(), nullable=False)
    identify = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return f'Ticket>>> {self.ticket_number} for {self.doctor.name}'
    
class TicketLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Text(), nullable=False)
    doctor_id = db.Column(db.Integer, nullable=False)
    ticket_number = db.Column(db.Integer, nullable=False)
    ticket_code = db.Column(db.String(10), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(1), nullable=False)  # '0', '1', or '2'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=False)
    identify = db.Column(db.Text(), nullable=False)

# Back relationship for the doctor
Doctor.tickets = db.relationship('Ticket', back_populates='doctor')
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One-to-one relationship to donor profile
    donor_profile = db.relationship('Donor', backref='user', uselist=False, cascade='all, delete-orphan')

    @property
    def uid(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username}>'

class Donor(db.Model):
    __tablename__ = 'donors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    last_donation_date = db.Column(db.Date, nullable=True) # Can be None if first time donor
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def uid(self):
        return str(self.id)

    @property
    def available(self):
        return self.is_available

    @available.setter
    def available(self, value):
        self.is_available = bool(value)

    @property
    def last_donation(self):
        return self.last_donation_date.strftime('%Y-%m-%d') if self.last_donation_date else ''

    @last_donation.setter
    def last_donation(self, value):
        if value:
            if isinstance(value, str):
                self.last_donation_date = datetime.strptime(value, '%Y-%m-%d').date()
            elif isinstance(value, (date, datetime)):
                self.last_donation_date = value
        else:
            self.last_donation_date = None

    def __repr__(self):
        return f'<Donor {self.name} - {self.blood_group}>'

class EmergencyRequest(db.Model):
    __tablename__ = 'emergency_requests'
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    blood_group = db.Column(db.String(10), nullable=False)
    hospital_name = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    units_needed = db.Column(db.Integer, default=1)
    required_by = db.Column(db.Date, nullable=False)
    is_fulfilled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def hospital(self):
        return self.hospital_name

    @hospital.setter
    def hospital(self, value):
        self.hospital_name = value

    @property
    def contact(self):
        return self.contact_phone

    @contact.setter
    def contact(self, value):
        self.contact_phone = value

    @property
    def description(self):
        return f"Urgent requirement of {self.blood_group} blood at {self.hospital_name}."

    @description.setter
    def description(self, value):
        pass

    def __repr__(self):
        return f'<EmergencyRequest {self.patient_name} - {self.blood_group}>'


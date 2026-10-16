from datetime import datetime
from extensions import db

class Airline(db.Model):
    __tablename__ = 'airlines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False, unique=True, index=True)
    callsign = db.Column(db.String(50), nullable=True)
    logo_color = db.Column(db.String(20), nullable=True, default='#1769FF')
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    flights = db.relationship('Flight', backref='airline', lazy='dynamic')

    def __repr__(self):
        return f'<Airline {self.code} - {self.name}>'

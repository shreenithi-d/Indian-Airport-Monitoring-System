from datetime import datetime
from extensions import db

class Airport(db.Model):
    __tablename__ = 'airports'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    state = db.Column(db.String(100), nullable=False, index=True)
    iata_code = db.Column(db.String(10), nullable=True, index=True)
    icao_code = db.Column(db.String(10), nullable=True, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False, default='Domestic')  # International, Domestic, Customs, Defense/Civil Enclave
    operational_status = db.Column(db.String(50), nullable=False, default='Operational')  # Operational, Non-Operational, Under Development
    description = db.Column(db.Text, nullable=True)
    terminals = db.Column(db.String(100), nullable=True, default='T1')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    departing_flights = db.relationship('Flight', foreign_keys='Flight.origin_airport_id', backref='origin_airport', lazy='dynamic')
    arriving_flights = db.relationship('Flight', foreign_keys='Flight.destination_airport_id', backref='destination_airport', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'state': self.state,
            'iata_code': self.iata_code or 'N/A',
            'icao_code': self.icao_code or 'N/A',
            'latitude': self.latitude,
            'longitude': self.longitude,
            'category': self.category,
            'operational_status': self.operational_status,
            'description': self.description or '',
            'terminals': self.terminals or 'T1',
            'departures_count': self.departing_flights.count(),
            'arrivals_count': self.arriving_flights.count()
        }

    def __repr__(self):
        return f'<Airport {self.iata_code or self.icao_code} - {self.name}>'

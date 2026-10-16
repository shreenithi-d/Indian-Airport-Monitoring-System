from datetime import datetime
from extensions import db

class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), nullable=False, index=True)
    airline_id = db.Column(db.Integer, db.ForeignKey('airlines.id'), nullable=False)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)
    origin_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    destination_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    
    scheduled_departure = db.Column(db.DateTime, nullable=False, index=True)
    scheduled_arrival = db.Column(db.DateTime, nullable=False)
    estimated_departure = db.Column(db.DateTime, nullable=True)
    estimated_arrival = db.Column(db.DateTime, nullable=True)
    actual_departure = db.Column(db.DateTime, nullable=True)
    actual_arrival = db.Column(db.DateTime, nullable=True)
    
    base_fare = db.Column(db.Float, nullable=False, default=4500.0)
    status = db.Column(db.String(30), nullable=False, default='Scheduled')  # Scheduled, Check-in open, Boarding, Departed, In flight, Arrived, Delayed, Cancelled
    terminal = db.Column(db.String(20), nullable=True, default='T1')
    gate = db.Column(db.String(20), nullable=True, default='G4')
    baggage_belt = db.Column(db.String(20), nullable=True, default='B2')
    data_source = db.Column(db.String(50), nullable=False, default='Reference Schedule')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='flight', lazy='dynamic')
    status_history = db.relationship('FlightStatusHistory', backref='flight', lazy='dynamic', cascade='all, delete-orphan', order_by='FlightStatusHistory.event_timestamp.desc()')
    seat_reservations = db.relationship('SeatReservation', backref='flight', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def duration_formatted(self):
        delta = self.scheduled_arrival - self.scheduled_departure
        total_minutes = int(delta.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"

    @property
    def available_seats_count(self):
        total_seats = self.aircraft.seats.filter_by(is_active=True, restriction_status='Available').count()
        reserved_seats = self.seat_reservations.filter(SeatReservation.reservation_status.in_(['Confirmed', 'Held'])).count()
        return max(0, total_seats - reserved_seats)

    def to_dict(self):
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'airline': self.airline.name,
            'airline_code': self.airline.code,
            'origin': {
                'id': self.origin_airport.id,
                'name': self.origin_airport.name,
                'city': self.origin_airport.city,
                'iata': self.origin_airport.iata_code,
                'lat': self.origin_airport.latitude,
                'lng': self.origin_airport.longitude
            },
            'destination': {
                'id': self.destination_airport.id,
                'name': self.destination_airport.name,
                'city': self.destination_airport.city,
                'iata': self.destination_airport.iata_code,
                'lat': self.destination_airport.latitude,
                'lng': self.destination_airport.longitude
            },
            'scheduled_departure': self.scheduled_departure.strftime('%Y-%m-%d %H:%M'),
            'scheduled_arrival': self.scheduled_arrival.strftime('%Y-%m-%d %H:%M'),
            'duration': self.duration_formatted,
            'base_fare': self.base_fare,
            'status': self.status,
            'terminal': self.terminal,
            'gate': self.gate,
            'aircraft': self.aircraft.model,
            'available_seats': self.available_seats_count
        }

    def __repr__(self):
        return f'<Flight {self.flight_number}: {self.origin_airport.iata_code} -> {self.destination_airport.iata_code}>'

class FlightStatusHistory(db.Model):
    __tablename__ = 'flight_status_history'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    previous_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    event_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50), default='Operational Schedule')
    notes = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<FlightStatusHistory {self.flight_id}: {self.previous_status} -> {self.new_status}>'

from models.booking import SeatReservation  # noqa: E402

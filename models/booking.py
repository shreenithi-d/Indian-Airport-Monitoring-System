from datetime import datetime
import secrets
import string
from extensions import db

def generate_booking_reference():
    chars = string.ascii_uppercase + string.digits
    rand_part = ''.join(secrets.choice(chars) for _ in range(6))
    return f"IN-{rand_part}"

class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_reference = db.Column(db.String(20), unique=True, nullable=False, index=True, default=generate_booking_reference)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False, index=True)
    
    booking_status = db.Column(db.String(30), nullable=False, default='Confirmed', index=True)  # Confirmed, Cancelled, Completed
    passenger_count = db.Column(db.Integer, nullable=False, default=1)
    
    base_fare_total = db.Column(db.Float, nullable=False, default=0.0)
    seat_charge_total = db.Column(db.Float, nullable=False, default=0.0)
    taxes_and_fees = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    
    payment_mode = db.Column(db.String(50), nullable=False, default='Demonstration Payment')
    payment_status = db.Column(db.String(30), nullable=False, default='Completed')  # Completed, Refunded, Pending
    
    cancellation_reason = db.Column(db.String(255), nullable=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    passengers = db.relationship('Passenger', backref='booking', lazy='dynamic', cascade='all, delete-orphan')
    seat_reservations = db.relationship('SeatReservation', backref='booking', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Booking {self.booking_reference} - {self.booking_status}>'

class Passenger(db.Model):
    __tablename__ = 'passengers'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    gender_selection = db.Column(db.String(20), nullable=False, default='Prefer not to say')  # 'Male', 'Female', 'Prefer not to say'
    age = db.Column(db.Integer, nullable=True)
    seat_number = db.Column(db.String(10), nullable=False)  # e.g. "12A"
    cabin_class = db.Column(db.String(30), nullable=False, default='Economy')

    # Relationships
    seat_reservation = db.relationship('SeatReservation', backref='passenger', uselist=False)

    def __repr__(self):
        return f'<Passenger {self.full_name} ({self.gender_selection}) Seat: {self.seat_number}>'

class SeatReservation(db.Model):
    __tablename__ = 'seat_reservations'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False, index=True)
    aircraft_seat_id = db.Column(db.Integer, db.ForeignKey('aircraft_seats.id'), nullable=False, index=True)
    passenger_id = db.Column(db.Integer, db.ForeignKey('passengers.id'), nullable=True, index=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True, index=True)
    
    reservation_status = db.Column(db.String(30), nullable=False, default='Confirmed', index=True)  # Confirmed, Held, Cancelled
    held_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    seat = db.relationship('AircraftSeat', backref='reservations')

    def __repr__(self):
        return f'<SeatReservation Flight:{self.flight_id} SeatID:{self.aircraft_seat_id} Status:{self.reservation_status}>'

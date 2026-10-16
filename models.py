from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db
import uuid


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' or 'admin'
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    passenger_profiles = db.relationship(
        'PassengerProfile', backref='user', lazy='dynamic', cascade='all, delete-orphan'
    )
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')
    notifications = db.relationship(
        'Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.email}>'


class Airport(db.Model):
    __tablename__ = 'airports'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    iata_code = db.Column(db.String(3), unique=True, nullable=True, index=True)
    icao_code = db.Column(db.String(4), unique=True, nullable=True, index=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False, default='India')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    airport_type = db.Column(db.String(50), default='Civil')  # Civil, Military, International, etc.
    classification = db.Column(db.String(20), default='Domestic')  # Domestic, International, Both
    operator = db.Column(db.String(200), default='Airports Authority of India')
    official_url = db.Column(db.String(500))
    terminal_info = db.Column(db.Text)   # JSON or text
    runway_info = db.Column(db.Text)     # JSON or text
    timezone = db.Column(db.String(50), default='Asia/Kolkata')
    description = db.Column(db.Text)
    operational_status = db.Column(db.String(30), default='Operational')  # Operational, Closed, Under Construction
    data_source = db.Column(db.String(255))
    source_url = db.Column(db.String(500))
    last_verified = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    historical_stats = db.relationship(
        'HistoricalAirportStat', backref='airport', lazy='dynamic', cascade='all, delete-orphan'
    )
    arrivals = db.relationship(
        'Flight', foreign_keys='Flight.destination_airport_id',
        backref='destination_airport', lazy='dynamic'
    )
    departures = db.relationship(
        'Flight', foreign_keys='Flight.origin_airport_id',
        backref='origin_airport', lazy='dynamic'
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'iata_code': self.iata_code,
            'icao_code': self.icao_code,
            'city': self.city,
            'state': self.state,
            'country': self.country,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'airport_type': self.airport_type,
            'classification': self.classification,
            'operator': self.operator,
            'official_url': self.official_url,
            'operational_status': self.operational_status,
            'description': self.description,
            'data_source': self.data_source,
            'last_verified': self.last_verified.isoformat() if self.last_verified else None,
        }

    def __repr__(self):
        return f'<Airport {self.iata_code} - {self.name}>'


class HistoricalAirportStat(db.Model):
    __tablename__ = 'historical_airport_stats'

    id = db.Column(db.Integer, primary_key=True)
    airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=False)
    reporting_year = db.Column(db.Integer, nullable=False)
    stat_type = db.Column(db.String(50), nullable=False)  # 'passenger', 'movement', 'cargo', 'milestone'
    value = db.Column(db.Float)
    unit = db.Column(db.String(30))   # 'million', 'tonnes', etc.
    description = db.Column(db.Text)
    source = db.Column(db.String(255))
    source_url = db.Column(db.String(500))
    last_updated = db.Column(db.DateTime, default=utcnow)

    __table_args__ = (db.Index('idx_airport_year', 'airport_id', 'reporting_year'),)

    def __repr__(self):
        return f'<HistoricalStat airport_id={self.airport_id} year={self.reporting_year}>'


class Flight(db.Model):
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    external_flight_id = db.Column(db.String(100))
    provider = db.Column(db.String(50), default='demo')
    flight_number = db.Column(db.String(20), nullable=False)
    airline = db.Column(db.String(150), nullable=False)
    airline_iata = db.Column(db.String(3))
    origin_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=True)
    destination_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'), nullable=True)
    origin_iata = db.Column(db.String(3))
    destination_iata = db.Column(db.String(3))
    scheduled_departure = db.Column(db.DateTime)
    scheduled_arrival = db.Column(db.DateTime)
    estimated_departure = db.Column(db.DateTime)
    estimated_arrival = db.Column(db.DateTime)
    actual_departure = db.Column(db.DateTime)
    actual_arrival = db.Column(db.DateTime)
    terminal = db.Column(db.String(20))
    gate = db.Column(db.String(20))
    status = db.Column(db.String(30), default='Scheduled')
    # Scheduled, Active, Landed, Delayed, Cancelled, Diverted
    aircraft = db.Column(db.String(50))
    cabin_class = db.Column(db.String(30), default='Economy')
    source = db.Column(db.String(50))
    is_demo = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    created_at = db.Column(db.DateTime, default=utcnow)

    # Relationships
    seats = db.relationship('Seat', backref='flight', lazy='dynamic', cascade='all, delete-orphan')
    flight_segments = db.relationship('FlightSegment', backref='flight', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'flight_number': self.flight_number,
            'airline': self.airline,
            'airline_iata': self.airline_iata,
            'origin_iata': self.origin_iata,
            'destination_iata': self.destination_iata,
            'scheduled_departure': self.scheduled_departure.isoformat() if self.scheduled_departure else None,
            'scheduled_arrival': self.scheduled_arrival.isoformat() if self.scheduled_arrival else None,
            'estimated_departure': self.estimated_departure.isoformat() if self.estimated_departure else None,
            'estimated_arrival': self.estimated_arrival.isoformat() if self.estimated_arrival else None,
            'actual_departure': self.actual_departure.isoformat() if self.actual_departure else None,
            'actual_arrival': self.actual_arrival.isoformat() if self.actual_arrival else None,
            'terminal': self.terminal,
            'gate': self.gate,
            'status': self.status,
            'aircraft': self.aircraft,
            'is_demo': self.is_demo,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }

    def __repr__(self):
        return f'<Flight {self.flight_number}>'


class PassengerProfile(db.Model):
    __tablename__ = 'passenger_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(10))   # Mr, Mrs, Ms, Dr, etc.
    given_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    surname = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    passenger_category = db.Column(db.String(20), default='adult')  # adult, child, infant
    gender_marker = db.Column(db.String(20))    # For travel documents: M, F — only if required
    gender_preference = db.Column(db.String(30))  # Self-declared optional preference
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    nationality = db.Column(db.String(100))
    passport_number_masked = db.Column(db.String(50))  # Masked: e.g. ****1234
    passport_expiry = db.Column(db.Date)
    passport_country = db.Column(db.String(100))
    # Encrypted/hashed passport number stored separately if needed (not implemented in demo)
    is_saved = db.Column(db.Boolean, default=True)   # False = one-time passenger, not saved long-term
    consent_given = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    booking_passengers = db.relationship('BookingPassenger', backref='passenger_profile', lazy='dynamic')

    def full_name(self):
        parts = [self.title, self.given_name, self.middle_name, self.surname]
        return ' '.join(p for p in parts if p)

    def __repr__(self):
        return f'<PassengerProfile {self.given_name} {self.surname}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    internal_booking_reference = db.Column(db.String(20), unique=True, nullable=False)
    provider_booking_reference = db.Column(db.String(100))   # From airline/GDS
    provider = db.Column(db.String(50), default='demo')
    booking_status = db.Column(db.String(30), default='draft')
    # Status: draft, pending_validation, reservation_requested, pending_provider_confirmation,
    #         confirmed, ticket_issued, failed, cancelled, refund_pending, refunded
    trip_type = db.Column(db.String(20), default='one_way')   # one_way, round_trip
    cabin_class = db.Column(db.String(30), default='Economy')
    currency = db.Column(db.String(3), default='INR')
    base_fare = db.Column(db.Float, default=0.0)
    taxes = db.Column(db.Float, default=0.0)
    seat_fees = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, default=0.0)
    is_demo = db.Column(db.Boolean, default=True)
    idempotency_key = db.Column(db.String(100), unique=True)
    provider_response_snapshot = db.Column(db.Text)   # JSON snapshot of provider response
    cancellation_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    booking_passengers = db.relationship(
        'BookingPassenger', backref='booking', lazy='dynamic', cascade='all, delete-orphan'
    )
    flight_segments = db.relationship(
        'FlightSegment', backref='booking', lazy='dynamic', cascade='all, delete-orphan'
    )
    notifications = db.relationship('Notification', backref='booking', lazy='dynamic')

    def __repr__(self):
        return f'<Booking {self.internal_booking_reference} {self.booking_status}>'


class BookingPassenger(db.Model):
    __tablename__ = 'booking_passengers'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    passenger_profile_id = db.Column(db.Integer, db.ForeignKey('passenger_profiles.id'), nullable=True)
    # Snapshot fields — captured at booking time, independent of profile edits:
    title = db.Column(db.String(10))
    given_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    surname = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    passenger_category = db.Column(db.String(20), default='adult')
    gender_marker = db.Column(db.String(5))   # M or F, only when required by provider
    nationality = db.Column(db.String(100))
    passport_number_masked = db.Column(db.String(50))
    passport_expiry = db.Column(db.Date)
    passport_country = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    seat_assignment = db.relationship(
        'SeatAssignment', backref='booking_passenger', uselist=False, cascade='all, delete-orphan'
    )
    created_at = db.Column(db.DateTime, default=utcnow)

    def full_name(self):
        parts = [self.title, self.given_name, self.middle_name, self.surname]
        return ' '.join(p for p in parts if p)

    def __repr__(self):
        return f'<BookingPassenger {self.given_name} {self.surname}>'


class FlightSegment(db.Model):
    __tablename__ = 'flight_segments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=True)
    provider_segment_id = db.Column(db.String(100))
    origin_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'))
    destination_airport_id = db.Column(db.Integer, db.ForeignKey('airports.id'))
    origin_iata = db.Column(db.String(3))
    destination_iata = db.Column(db.String(3))
    departure_time = db.Column(db.DateTime)
    arrival_time = db.Column(db.DateTime)
    cabin_class = db.Column(db.String(30))
    flight_number = db.Column(db.String(20))
    airline = db.Column(db.String(150))
    segment_order = db.Column(db.Integer, default=0)   # 0=outbound, 1=return

    # Relationships
    seat_assignments = db.relationship(
        'SeatAssignment', backref='flight_segment', lazy='dynamic', cascade='all, delete-orphan'
    )
    origin_airport = db.relationship('Airport', foreign_keys=[origin_airport_id])
    destination_airport = db.relationship('Airport', foreign_keys=[destination_airport_id])

    def __repr__(self):
        return f'<FlightSegment {self.flight_number} {self.origin_iata}->{self.destination_iata}>'


class Seat(db.Model):
    __tablename__ = 'seats'

    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False)
    provider_seat_id = db.Column(db.String(50))
    seat_number = db.Column(db.String(10), nullable=False)   # e.g. '14A'
    row_number = db.Column(db.Integer)
    column_letter = db.Column(db.String(3))
    cabin = db.Column(db.String(30), default='Economy')
    seat_type = db.Column(db.String(30))   # window, middle, aisle
    seat_attributes = db.Column(db.Text)   # JSON list: ['extra_legroom', 'exit_row']
    availability_status = db.Column(db.String(20), default='available')
    # available, occupied, restricted, blocked
    seat_fee = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='INR')
    source = db.Column(db.String(50))
    is_demo = db.Column(db.Boolean, default=True)
    last_updated = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        db.UniqueConstraint('flight_id', 'seat_number', name='uq_flight_seat'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'seat_number': self.seat_number,
            'row_number': self.row_number,
            'column_letter': self.column_letter,
            'cabin': self.cabin,
            'seat_type': self.seat_type,
            'availability_status': self.availability_status,
            'seat_fee': self.seat_fee,
            'currency': self.currency,
            'is_demo': self.is_demo,
        }

    def __repr__(self):
        return f'<Seat {self.seat_number} flight_id={self.flight_id}>'


class SeatAssignment(db.Model):
    __tablename__ = 'seat_assignments'

    id = db.Column(db.Integer, primary_key=True)
    booking_passenger_id = db.Column(
        db.Integer, db.ForeignKey('booking_passengers.id'), nullable=False, unique=True
    )
    flight_segment_id = db.Column(db.Integer, db.ForeignKey('flight_segments.id'), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seats.id'), nullable=True)
    seat_number = db.Column(db.String(10))   # Snapshot
    assignment_status = db.Column(db.String(20), default='pending')
    # pending, confirmed, cancelled
    seat_fee = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='INR')
    provider_assignment_reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Prevent two confirmed assignments for same seat on same segment
    __table_args__ = (
        db.Index('idx_segment_seat', 'flight_segment_id', 'seat_id'),
    )

    seat = db.relationship('Seat')

    def __repr__(self):
        return f'<SeatAssignment passenger={self.booking_passenger_id} seat={self.seat_number}>'


class APIDataLog(db.Model):
    __tablename__ = 'api_data_logs'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50))
    endpoint_category = db.Column(db.String(50))
    # airports, arrivals, departures, flight_search, booking, etc.
    request_time = db.Column(db.DateTime, default=utcnow)
    response_status = db.Column(db.Integer)
    success = db.Column(db.Boolean, default=False)
    response_time_ms = db.Column(db.Integer)
    sanitized_error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f'<APIDataLog {self.provider} {self.endpoint_category} {self.response_status}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    notification_type = db.Column(db.String(50))
    # booking_received, booking_confirmed, booking_failed, etc.
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f'<Notification user_id={self.user_id} type={self.notification_type}>'


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource_type = db.Column(db.String(50))
    resource_id = db.Column(db.Integer)
    details = db.Column(db.Text)   # JSON, sanitized
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=utcnow)

    def __repr__(self):
        return f'<AuditLog {self.action} by user_id={self.user_id}>'

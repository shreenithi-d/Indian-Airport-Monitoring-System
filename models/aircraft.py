from datetime import datetime
from extensions import db

class Aircraft(db.Model):
    __tablename__ = 'aircraft'

    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(100), nullable=False)  # e.g. Airbus A320neo, Boeing 737-800
    registration = db.Column(db.String(50), nullable=False, unique=True)  # e.g. VT-INA
    seat_capacity = db.Column(db.Integer, nullable=False, default=180)
    layout_configuration = db.Column(db.String(20), nullable=False, default='3-3')  # '3-3' or '2-2'
    total_rows = db.Column(db.Integer, nullable=False, default=30)
    active_status = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    seats = db.relationship('AircraftSeat', backref='aircraft', lazy='dynamic', cascade='all, delete-orphan')
    flights = db.relationship('Flight', backref='aircraft', lazy='dynamic')

    def __repr__(self):
        return f'<Aircraft {self.registration} ({self.model})>'

class AircraftSeat(db.Model):
    __tablename__ = 'aircraft_seats'

    id = db.Column(db.Integer, primary_key=True)
    aircraft_id = db.Column(db.Integer, db.ForeignKey('aircraft.id'), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)
    seat_letter = db.Column(db.String(2), nullable=False)  # 'A', 'B', 'C', 'D', 'E', 'F'
    cabin_class = db.Column(db.String(30), nullable=False, default='Economy')  # Economy, Business, Premium Economy
    seat_type = db.Column(db.String(30), nullable=False, default='Standard')  # Window, Middle, Aisle, Extra Legroom, Emergency Exit
    additional_charge = db.Column(db.Float, nullable=False, default=0.0)
    restriction_status = db.Column(db.String(20), nullable=False, default='Available')  # Available, Restricted, Blocked
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.UniqueConstraint('aircraft_id', 'row_number', 'seat_letter', name='uix_aircraft_seat'),
    )

    @property
    def seat_code(self):
        return f"{self.row_number}{self.seat_letter}"

    def __repr__(self):
        return f'<Seat {self.seat_code} - Aircraft {self.aircraft_id}>'

from models.flight import Flight
from models.aircraft import AircraftSeat
from models.booking import Booking, Passenger, SeatReservation
from services.seat_service import get_flight_seat_map, validate_seats_available
from extensions import db

def test_seat_map_generation(app):
    with app.app_context():
        flight = Flight.query.first()
        seat_map = get_flight_seat_map(flight.id)

        assert seat_map is not None
        assert seat_map['total_seats'] == 180
        assert len(seat_map['rows']) == 30
        assert seat_map['seat_letters'] == ['A', 'B', 'C', 'D', 'E', 'F']

def test_male_blue_and_female_pink_seat_assignments(app):
    with app.app_context():
        flight = Flight.query.first()
        seat_2a = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=2, seat_letter='A').first()
        seat_2b = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=2, seat_letter='B').first()
        seat_2c = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=2, seat_letter='C').first()

        # Create dummy booking
        booking = Booking(
            booking_reference="IN-TEST-SEAT",
            user_id=1,
            flight_id=flight.id,
            booking_status="Confirmed",
            passenger_count=3
        )
        db.session.add(booking)
        db.session.flush()

        # Passenger 1: Male -> 2A
        pax_male = Passenger(
            booking_id=booking.id,
            full_name="Male Traveler",
            gender_selection="Male",
            age=30,
            seat_number=seat_2a.seat_code
        )
        db.session.add(pax_male)
        db.session.flush()

        res_male = SeatReservation(
            flight_id=flight.id,
            aircraft_seat_id=seat_2a.id,
            passenger_id=pax_male.id,
            booking_id=booking.id,
            reservation_status="Confirmed"
        )
        db.session.add(res_male)

        # Passenger 2: Female -> 2B
        pax_female = Passenger(
            booking_id=booking.id,
            full_name="Female Traveler",
            gender_selection="Female",
            age=28,
            seat_number=seat_2b.seat_code
        )
        db.session.add(pax_female)
        db.session.flush()

        res_female = SeatReservation(
            flight_id=flight.id,
            aircraft_seat_id=seat_2b.id,
            passenger_id=pax_female.id,
            booking_id=booking.id,
            reservation_status="Confirmed"
        )
        db.session.add(res_female)

        # Passenger 3: Prefer not to say -> 2C
        pax_other = Passenger(
            booking_id=booking.id,
            full_name="Other Traveler",
            gender_selection="Prefer not to say",
            age=25,
            seat_number=seat_2c.seat_code
        )
        db.session.add(pax_other)
        db.session.flush()

        res_other = SeatReservation(
            flight_id=flight.id,
            aircraft_seat_id=seat_2c.id,
            passenger_id=pax_other.id,
            booking_id=booking.id,
            reservation_status="Confirmed"
        )
        db.session.add(res_other)
        db.session.commit()

        # Retrieve flight seat map and verify visual assignment tags
        seat_map = get_flight_seat_map(flight.id)
        row_2 = next(r for r in seat_map['rows'] if r['row_number'] == 2)
        seat_2a_data = next(s for s in row_2['seats'] if s['letter'] == 'A')
        seat_2b_data = next(s for s in row_2['seats'] if s['letter'] == 'B')
        seat_2c_data = next(s for s in row_2['seats'] if s['letter'] == 'C')

        # EXACT REQUIRED GENDER-BASED COLORS:
        # Male passenger assignment -> 'male' (corresponds to CSS #DCEBFF / #4385E8)
        assert seat_2a_data['gender_color'] == 'male'
        assert seat_2a_data['state'] == 'occupied'

        # Female passenger assignment -> 'female' (corresponds to CSS #FFE0EC / #E66B9A)
        assert seat_2b_data['gender_color'] == 'female'
        assert seat_2b_data['state'] == 'occupied'

        # Prefer not to say -> 'other' (neutral gray)
        assert seat_2c_data['gender_color'] == 'other'
        assert seat_2c_data['state'] == 'occupied'

def test_occupied_seat_rejection_and_duplicate_prevention(app):
    with app.app_context():
        flight = Flight.query.first()
        seat_2a = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=2, seat_letter='A').first()

        # Reserve seat 2A
        res = SeatReservation(
            flight_id=flight.id,
            aircraft_seat_id=seat_2a.id,
            reservation_status="Confirmed"
        )
        db.session.add(res)
        db.session.commit()

        # Attempt to validate or book seat 2A again
        is_valid, msg = validate_seats_available(flight.id, [seat_2a.id])
        assert is_valid is False
        assert "already booked or held" in msg

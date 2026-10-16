from models.flight import Flight
from models.user import User
from models.aircraft import AircraftSeat
from models.booking import Booking, SeatReservation
from services.booking_service import (
    calculate_booking_breakdown,
    create_booking_transaction,
    cancel_booking_transaction
)

def test_booking_creation_transaction(app):
    with app.app_context():
        user = User.query.filter_by(role='passenger').first()
        flight = Flight.query.first()

        # Select available seats (Row 10, seats A and B)
        seat_10a = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=10, seat_letter='A').first()
        seat_10b = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=10, seat_letter='B').first()

        passengers_data = [
            {
                'seat_id': seat_10a.id,
                'full_name': 'Amit Kumar',
                'gender_selection': 'Male',
                'age': 35
            },
            {
                'seat_id': seat_10b.id,
                'full_name': 'Neha Kumar',
                'gender_selection': 'Female',
                'age': 32
            }
        ]

        # 1. Authoritative price breakdown check
        breakdown = calculate_booking_breakdown(flight, passengers_data)
        assert breakdown['passenger_count'] == 2
        assert breakdown['base_fare_total'] == flight.base_fare * 2
        assert breakdown['udf'] == 500.0  # ₹250 * 2
        assert breakdown['total_amount'] > (flight.base_fare * 2)

        # 2. Transaction creation
        booking, msg = create_booking_transaction(
            user_id=user.id,
            flight_id=flight.id,
            passengers_data=passengers_data
        )

        assert booking is not None
        assert booking.booking_status == 'Confirmed'
        assert booking.booking_reference.startswith('IN-')
        assert booking.passenger_count == 2
        assert len(booking.passengers.all()) == 2
        assert len(booking.seat_reservations.all()) == 2

        # 3. Check seats are now reserved in database
        res_10a = SeatReservation.query.filter_by(flight_id=flight.id, aircraft_seat_id=seat_10a.id, reservation_status='Confirmed').first()
        assert res_10a is not None

def test_booking_cancellation_and_seat_release(app):
    with app.app_context():
        user = User.query.filter_by(role='passenger').first()
        flight = Flight.query.first()
        seat_11a = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=11, seat_letter='A').first()

        booking, msg = create_booking_transaction(
            user_id=user.id,
            flight_id=flight.id,
            passengers_data=[{
                'seat_id': seat_11a.id,
                'full_name': 'Cancel Test User',
                'gender_selection': 'Male',
                'age': 40
            }]
        )
        assert booking is not None

        # Verify seat reserved
        res = SeatReservation.query.filter_by(flight_id=flight.id, aircraft_seat_id=seat_11a.id, reservation_status='Confirmed').first()
        assert res is not None

        # Cancel booking
        success, cancel_msg = cancel_booking_transaction(booking.id, user_id=user.id, reason="Testing cancellation")
        assert success is True
        assert booking.booking_status == 'Cancelled'

        # Verify seat released
        active_res = SeatReservation.query.filter_by(flight_id=flight.id, aircraft_seat_id=seat_11a.id, reservation_status='Confirmed').first()
        assert active_res is None

def test_booking_ownership_restriction(app):
    with app.app_context():
        flight = Flight.query.first()
        seat_12a = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, row_number=12, seat_letter='A').first()
        
        # Booking created by user 2 (passenger)
        booking, msg = create_booking_transaction(
            user_id=2,
            flight_id=flight.id,
            passengers_data=[{'seat_id': seat_12a.id, 'full_name': 'User Two', 'gender_selection': 'Male', 'age': 25}]
        )
        assert booking is not None

        # User 99 attempts to cancel user 2's booking without admin rights
        success, cancel_msg = cancel_booking_transaction(booking.id, user_id=99, is_admin=False)
        assert success is False
        assert "Unauthorized" in cancel_msg

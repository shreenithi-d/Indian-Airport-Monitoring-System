from datetime import datetime
from extensions import db
from models.booking import Booking, Passenger, SeatReservation
from models.flight import Flight
from models.aircraft import AircraftSeat
from models.notification import Notification
from models.audit_log import AuditLog
from services.seat_service import validate_seats_available

def calculate_booking_breakdown(flight, passengers_data):
    """
    Computes server-authoritative fare breakdown:
    - Base fare
    - Seat selection charges
    - Aviation GST (5%) & User Development Fee (₹250 per pax)
    """
    pax_count = len(passengers_data)
    base_fare_total = round(flight.base_fare * pax_count, 2)
    
    seat_charge_total = 0.0
    for p in passengers_data:
        seat_id = p.get('seat_id')
        if seat_id:
            seat = AircraftSeat.query.get(seat_id)
            if seat:
                seat_charge_total += seat.additional_charge
    seat_charge_total = round(seat_charge_total, 2)

    gst = round((base_fare_total + seat_charge_total) * 0.05, 2)
    udf = round(250.0 * pax_count, 2)
    taxes_and_fees = round(gst + udf, 2)

    total_amount = round(base_fare_total + seat_charge_total + taxes_and_fees, 2)

    return {
        'passenger_count': pax_count,
        'base_fare_total': base_fare_total,
        'seat_charge_total': seat_charge_total,
        'taxes_and_fees': taxes_and_fees,
        'gst': gst,
        'udf': udf,
        'total_amount': total_amount
    }

def create_booking_transaction(user_id, flight_id, passengers_data, payment_mode='Demonstration Payment'):
    """
    Executes atomic database transaction for booking creation:
    - Validates seat availability
    - Inserts Booking
    - Inserts Passenger records
    - Inserts SeatReservation records
    - Prevents race conditions and double bookings
    """
    flight = Flight.query.get(flight_id)
    if not flight:
        return None, "Flight not found."

    if not passengers_data or len(passengers_data) == 0:
        return None, "At least one passenger is required."

    seat_ids = [p['seat_id'] for p in passengers_data if 'seat_id' in p]
    if len(seat_ids) != len(passengers_data):
        return None, "All passengers must have an assigned seat."

    if len(seat_ids) != len(set(seat_ids)):
        return None, "Duplicate seat selection within the same booking."

    # Validate seat availability against database
    is_valid, result = validate_seats_available(flight_id, seat_ids)
    if not is_valid:
        return None, result

    # Authoritative price calculation
    breakdown = calculate_booking_breakdown(flight, passengers_data)

    try:
        booking = Booking(
            user_id=user_id,
            flight_id=flight_id,
            booking_status='Confirmed',
            passenger_count=len(passengers_data),
            base_fare_total=breakdown['base_fare_total'],
            seat_charge_total=breakdown['seat_charge_total'],
            taxes_and_fees=breakdown['taxes_and_fees'],
            total_amount=breakdown['total_amount'],
            payment_mode=payment_mode,
            payment_status='Completed'
        )
        db.session.add(booking)
        db.session.flush()

        # Add passengers and seat reservations
        for p_info in passengers_data:
            seat = AircraftSeat.query.get(p_info['seat_id'])
            pax = Passenger(
                booking_id=booking.id,
                full_name=p_info['full_name'].strip(),
                gender_selection=p_info.get('gender_selection', 'Prefer not to say'),
                age=int(p_info.get('age', 30)),
                seat_number=seat.seat_code,
                cabin_class=seat.cabin_class
            )
            db.session.add(pax)
            db.session.flush()

            # Reserve seat
            reservation = SeatReservation(
                flight_id=flight_id,
                aircraft_seat_id=seat.id,
                passenger_id=pax.id,
                booking_id=booking.id,
                reservation_status='Confirmed'
            )
            db.session.add(reservation)

        # In-app notification
        notification = Notification(
            user_id=user_id,
            title='Booking Confirmed',
            message=f"Your booking {booking.booking_reference} for flight {flight.flight_number} ({flight.origin_airport.city} to {flight.destination_airport.city}) has been confirmed successfully.",
            notification_type='booking'
        )
        db.session.add(notification)

        # Audit log
        audit = AuditLog(
            actor_user_id=user_id,
            action='CREATE_BOOKING',
            entity_type='Booking',
            entity_id=booking.id,
            notes=f"Confirmed booking {booking.booking_reference} for flight {flight.flight_number} with {len(passengers_data)} passengers."
        )
        db.session.add(audit)

        db.session.commit()
        return booking, "Booking confirmed successfully."
    except Exception as e:
        db.session.rollback()
        return None, f"Booking transaction failed: {str(e)}"

def cancel_booking_transaction(booking_id, user_id=None, is_admin=False, reason=None):
    """
    Cancels a booking, releases seat reservations, records audit and notification.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return False, "Booking not found."

    if not is_admin and booking.user_id != user_id:
        return False, "Unauthorized access to this booking."

    if booking.booking_status == 'Cancelled':
        return False, "This booking is already cancelled."

    try:
        booking.booking_status = 'Cancelled'
        booking.payment_status = 'Refunded'
        booking.cancelled_at = datetime.utcnow()
        booking.cancellation_reason = reason or "Cancelled by user"

        # Release all seat reservations
        for res in booking.seat_reservations:
            res.reservation_status = 'Cancelled'

        # Send notification
        notification = Notification(
            user_id=booking.user_id,
            title='Booking Cancelled',
            message=f"Booking {booking.booking_reference} for flight {booking.flight.flight_number} has been cancelled. Allocated seats have been released.",
            notification_type='booking'
        )
        db.session.add(notification)

        # Audit log
        audit = AuditLog(
            actor_user_id=user_id,
            action='CANCEL_BOOKING',
            entity_type='Booking',
            entity_id=booking.id,
            notes=f"Booking {booking.booking_reference} cancelled. Reason: {booking.cancellation_reason}"
        )
        db.session.add(audit)

        db.session.commit()
        return True, "Booking has been cancelled and seats released."
    except Exception as e:
        db.session.rollback()
        return False, f"Cancellation failed: {str(e)}"

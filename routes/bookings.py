from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from flask_login import login_required, current_user
from extensions import db
from models.flight import Flight
from models.aircraft import AircraftSeat
from models.booking import Booking
from services.booking_service import (
    calculate_booking_breakdown,
    create_booking_transaction,
    cancel_booking_transaction
)
from services.flight_service import get_flight_by_id

bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/booking/passengers', methods=['GET', 'POST'])
@login_required
def enter_passengers():
    flight_id = request.args.get('flight_id', type=int) or request.form.get('flight_id', type=int)
    seat_ids_raw = request.args.get('seat_ids', '') or request.form.get('seat_ids', '')

    if not flight_id or not seat_ids_raw:
        flash("Invalid booking session. Please select your flight and seats.", "warning")
        return redirect(url_for('flights.search'))

    flight = get_flight_by_id(flight_id)
    if not flight:
        abort(404)

    try:
        seat_ids = [int(s.strip()) for s in seat_ids_raw.split(',') if s.strip()]
    except ValueError:
        flash("Invalid seat identifiers.", "danger")
        return redirect(url_for('seats.seat_selection', flight_id=flight.id))

    selected_seats = AircraftSeat.query.filter(AircraftSeat.id.in_(seat_ids)).all()
    if len(selected_seats) != len(seat_ids):
        flash("One or more selected seats could not be found.", "danger")
        return redirect(url_for('seats.seat_selection', flight_id=flight.id))

    if request.method == 'POST' and request.form.get('action') == 'proceed_to_review':
        # Collect passenger details
        passengers_data = []
        has_error = False

        for idx, seat in enumerate(selected_seats, start=1):
            name = request.form.get(f'name_{seat.id}', '').strip()
            gender = request.form.get(f'gender_{seat.id}', 'Prefer not to say')
            age_val = request.form.get(f'age_{seat.id}', '30').strip()

            if not name:
                flash(f"Please provide full name for passenger assigned to Seat {seat.seat_code}.", "danger")
                has_error = True
                break

            try:
                age = int(age_val)
                if age < 1 or age > 120:
                    raise ValueError
            except ValueError:
                flash(f"Please provide a valid age for passenger on Seat {seat.seat_code}.", "danger")
                has_error = True
                break

            passengers_data.append({
                'seat_id': seat.id,
                'seat_code': seat.seat_code,
                'full_name': name,
                'gender_selection': gender,
                'age': age
            })

        if has_error:
            return render_template(
                'passenger_details.html',
                flight=flight,
                seats=selected_seats,
                seat_ids_raw=seat_ids_raw
            )

        # Store in session for review step
        session['booking_draft'] = {
            'flight_id': flight.id,
            'passengers': passengers_data
        }
        return redirect(url_for('bookings.review_booking'))

    return render_template(
        'passenger_details.html',
        flight=flight,
        seats=selected_seats,
        seat_ids_raw=seat_ids_raw
    )

@bookings_bp.route('/booking/review', methods=['GET'])
@login_required
def review_booking():
    draft = session.get('booking_draft')
    if not draft:
        flash("No active booking found. Please initiate flight and seat selection.", "info")
        return redirect(url_for('flights.search'))

    flight = get_flight_by_id(draft['flight_id'])
    if not flight:
        abort(404)

    passengers_data = draft['passengers']
    breakdown = calculate_booking_breakdown(flight, passengers_data)

    return render_template(
        'booking_review.html',
        flight=flight,
        passengers=passengers_data,
        breakdown=breakdown
    )

@bookings_bp.route('/booking/confirm', methods=['POST'])
@login_required
def confirm_booking():
    draft = session.get('booking_draft')
    if not draft:
        flash("No active booking session found.", "danger")
        return redirect(url_for('flights.search'))

    payment_mode = request.form.get('payment_mode', 'Demonstration Payment')

    booking, message = create_booking_transaction(
        user_id=current_user.id,
        flight_id=draft['flight_id'],
        passengers_data=draft['passengers'],
        payment_mode=payment_mode
    )

    if not booking:
        flash(message, "danger")
        return redirect(url_for('bookings.review_booking'))

    # Clear draft session
    session.pop('booking_draft', None)

    flash(f"Booking {booking.booking_reference} confirmed successfully!", "success")
    return redirect(url_for('bookings.booking_confirmation', booking_id=booking.id))

@bookings_bp.route('/booking/confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        abort(404)

    if booking.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    return render_template('booking_confirmation.html', booking=booking)

@bookings_bp.route('/booking/ticket/<int:booking_id>')
@login_required
def ticket_view(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        abort(404)

    if booking.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    return render_template('ticket_view.html', booking=booking)

@bookings_bp.route('/my-bookings')
@login_required
def my_bookings():
    status_filter = request.args.get('status', 'All')
    search_ref = request.args.get('search', '').strip()

    query = Booking.query.filter_by(user_id=current_user.id)

    if status_filter != 'All':
        query = query.filter_by(booking_status=status_filter)
    if search_ref:
        query = query.filter(Booking.booking_reference.ilike(f"%{search_ref}%"))

    bookings = query.order_by(Booking.created_at.desc()).all()

    return render_template(
        'my_bookings.html',
        bookings=bookings,
        selected_status=status_filter,
        search=search_ref
    )

@bookings_bp.route('/booking/<int:booking_id>')
@login_required
def booking_details(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        abort(404)

    if booking.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    return render_template('booking_details.html', booking=booking)

@bookings_bp.route('/booking/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    reason = request.form.get('reason', 'Cancelled by user')
    success, message = cancel_booking_transaction(
        booking_id=booking_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin,
        reason=reason
    )

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(url_for('bookings.booking_details', booking_id=booking_id))

from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from flask_login import current_user
from models.flight import Flight
from services.flight_service import get_flight_by_id
from services.seat_service import get_flight_seat_map

seats_bp = Blueprint('seats', __name__)

@seats_bp.route('/flights/<int:flight_id>/seats')
def seat_selection(flight_id):
    flight = get_flight_by_id(flight_id)
    if not flight:
        abort(404)

    passengers_count = request.args.get('passengers', 1, type=int)
    if passengers_count < 1:
        passengers_count = 1
    elif passengers_count > 9:
        passengers_count = 9

    seat_map_data = get_flight_seat_map(flight.id, current_user.id if current_user.is_authenticated else None)

    return render_template(
        'seat_selection.html',
        flight=flight,
        seat_map=seat_map_data,
        passengers_count=passengers_count
    )

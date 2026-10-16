from flask import Blueprint, jsonify, request
from extensions import db
from models.airport import Airport
from models.flight import Flight
from models.booking import Booking
from services.seat_service import get_flight_seat_map
from services.flight_service import get_flight_route_coordinates

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/airports')
def get_airports():
    category = request.args.get('category')
    state = request.args.get('state')
    status = request.args.get('status')
    search = request.args.get('search')

    query = Airport.query
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                Airport.name.ilike(s),
                Airport.city.ilike(s),
                Airport.state.ilike(s),
                Airport.iata_code.ilike(s),
                Airport.icao_code.ilike(s)
            )
        )
    if category and category != 'All':
        query = query.filter_by(category=category)
    if state and state != 'All':
        query = query.filter_by(state=state)
    if status and status != 'All':
        query = query.filter_by(operational_status=status)

    airports = query.all()
    return jsonify([a.to_dict() for a in airports])

@api_bp.route('/airports/<int:airport_id>')
def get_airport(airport_id):
    airport = Airport.query.get(airport_id)
    if not airport:
        return jsonify({'error': 'Airport not found'}), 404
    return jsonify(airport.to_dict())

@api_bp.route('/flights/route/<int:flight_id>')
def get_flight_route(flight_id):
    flight = Flight.query.get(flight_id)
    if not flight:
        return jsonify({'error': 'Flight not found'}), 404
    return jsonify(get_flight_route_coordinates(flight))

@api_bp.route('/flights/<int:flight_id>/seat-map')
def get_seat_map(flight_id):
    seat_data = get_flight_seat_map(flight_id)
    if not seat_data:
        return jsonify({'error': 'Seat map not found'}), 404
    return jsonify(seat_data)

@api_bp.route('/analytics/charts')
def analytics_charts():
    # 1. Airport Category Distribution
    cat_query = db.session.query(Airport.category, db.func.count(Airport.id)).group_by(Airport.category).all()
    categories = [c[0] for c in cat_query]
    cat_counts = [c[1] for c in cat_query]

    # 2. Flight Status Distribution
    status_query = db.session.query(Flight.status, db.func.count(Flight.id)).group_by(Flight.status).all()
    statuses = [s[0] for s in status_query]
    status_counts = [s[1] for s in status_query]

    # 3. Booking Status Breakdown
    book_query = db.session.query(Booking.booking_status, db.func.count(Booking.id)).group_by(Booking.booking_status).all()
    booking_statuses = [b[0] for b in book_query]
    booking_counts = [b[1] for b in book_query]

    # 4. Top Routes
    top_flights = Flight.query.limit(5).all()
    route_labels = [f"{f.origin_airport.city} -> {f.destination_airport.city}" for f in top_flights]
    route_counts = [f.bookings.count() for f in top_flights]

    return jsonify({
        'categories': {'labels': categories, 'data': cat_counts},
        'flight_statuses': {'labels': statuses, 'data': status_counts},
        'booking_statuses': {'labels': booking_statuses, 'data': booking_counts},
        'top_routes': {'labels': route_labels, 'data': route_counts}
    })

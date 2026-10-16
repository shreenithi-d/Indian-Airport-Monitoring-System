from flask import Blueprint, render_template, request, jsonify, abort
from extensions import db
from models.airport import Airport
from models.flight import Flight
from services.airport_service import (
    get_all_airports,
    get_airport_by_id,
    get_nearby_airports
)
from services.flight_service import (
    get_departures_for_airport,
    get_arrivals_for_airport
)

airports_bp = Blueprint('airports', __name__)

@airports_bp.route('/airports/map')
def map_view():
    """Main interactive geographical airport map dashboard."""
    # Retrieve all operational states for filter dropdown
    states = db.session.query(Airport.state).distinct().order_by(Airport.state.asc()).all()
    states_list = [s[0] for s in states if s[0]]

    # Initial airports list
    airports = Airport.query.order_by(Airport.city.asc()).all()
    
    # Pre-select an airport if id passed in query param
    selected_id = request.args.get('selected_id', type=int)
    selected_airport = Airport.query.get(selected_id) if selected_id else None

    return render_template(
        'airport_map.html',
        airports=airports,
        airports_json=[a.to_dict() for a in airports],
        states=states_list,
        selected_airport=selected_airport
    )

@airports_bp.route('/airports')
def airport_list():
    """Directory listing of all registered Indian airports with pagination and filters."""
    category = request.args.get('category', 'All')
    state = request.args.get('state', 'All')
    status = request.args.get('status', 'All')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 15

    query = Airport.query

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Airport.name.ilike(search_term),
                Airport.city.ilike(search_term),
                Airport.state.ilike(search_term),
                Airport.iata_code.ilike(search_term),
                Airport.icao_code.ilike(search_term)
            )
        )
    if category != 'All':
        query = query.filter_by(category=category)
    if state != 'All':
        query = query.filter_by(state=state)
    if status != 'All':
        query = query.filter_by(operational_status=status)

    pagination = query.order_by(Airport.city.asc()).paginate(page=page, per_page=per_page, error_out=False)

    states = [s[0] for s in db.session.query(Airport.state).distinct().order_by(Airport.state.asc()).all() if s[0]]

    return render_template(
        'airport_directory.html',
        pagination=pagination,
        airports=pagination.items,
        states=states,
        selected_category=category,
        selected_state=state,
        selected_status=status,
        search=search
    )

@airports_bp.route('/airports/<int:airport_id>')
def airport_details(airport_id):
    """Detailed airport profile with scheduled flights and nearby nodes."""
    airport = get_airport_by_id(airport_id)
    if not airport:
        abort(404)

    departures = get_departures_for_airport(airport.id, limit=10)
    arrivals = get_arrivals_for_airport(airport.id, limit=10)
    nearby = get_nearby_airports(airport, max_km=450, limit=4)

    return render_template(
        'airport_details.html',
        airport=airport,
        departures=departures,
        arrivals=arrivals,
        nearby_airports=nearby
    )

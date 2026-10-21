from flask import Blueprint, render_template, request, abort
from datetime import datetime
from extensions import db
from models.flight import Flight
from models.airport import Airport
from models.airline import Airline
from services.flight_service import (
    search_flights,
    get_flight_by_id,
    get_flight_route_coordinates,
    get_flight_status_timeline
)

flights_bp = Blueprint('flights', __name__)

@flights_bp.route('/flights/search')
def search():
    origin_id = request.args.get('origin_id', type=int)
    dest_id = request.args.get('destination_id', type=int)
    travel_date = request.args.get('travel_date', '')
    passengers_count = request.args.get('passengers', 1, type=int)
    cabin_class = request.args.get('cabin_class', 'Economy')
    airline_id = request.args.get('airline_id', type=int)
    sort_by = request.args.get('sort_by', 'fare')

    # If origin and dest are provided and identical, handle gracefully
    same_airport_error = False
    if origin_id and dest_id and origin_id == dest_id:
        same_airport_error = True
        flights = []
    else:
        flights = search_flights(
            origin_id=origin_id,
            destination_id=dest_id,
            travel_date=travel_date,
            cabin_class=cabin_class,
            airline_id=airline_id,
            sort_by=sort_by
        )

    all_airports = Airport.query.filter_by(operational_status='Operational').order_by(Airport.city.asc()).all()
    all_airlines = Airline.query.order_by(Airline.name.asc()).all()

    origin_airport = Airport.query.get(origin_id) if origin_id else None
    dest_airport = Airport.query.get(dest_id) if dest_id else None

    return render_template(
        'flight_search.html',
        flights=flights,
        airports=all_airports,
        airlines=all_airlines,
        selected_origin=origin_airport,
        selected_dest=dest_airport,
        travel_date=travel_date,
        passengers_count=passengers_count,
        cabin_class=cabin_class,
        selected_airline_id=airline_id,
        sort_by=sort_by,
        same_airport_error=same_airport_error
    )

@flights_bp.route('/flights/<int:flight_id>')
def details(flight_id):
    flight = get_flight_by_id(flight_id)
    if not flight:
        abort(404)

    route_info = get_flight_route_coordinates(flight)
    timeline = get_flight_status_timeline(flight)
    passengers_count = request.args.get('passengers', 1, type=int)

    return render_template(
        'flight_details.html',
        flight=flight,
        route_info=route_info,
        timeline=timeline,
        passengers_count=passengers_count
    )

@flights_bp.route('/flights/track')
def track_search():
    flight_num = request.args.get('flight_number', '').strip().upper()
    status_filter = request.args.get('status', 'All')
    origin_id = request.args.get('origin_id', type=int)
    dest_id = request.args.get('dest_id', type=int)
    airline_id = request.args.get('airline_id', type=int)

    query = Flight.query
    if flight_num:
        query = query.filter(Flight.flight_number.ilike(f"%{flight_num}%"))
    if status_filter != 'All':
        query = query.filter_by(status=status_filter)
    if origin_id:
        query = query.filter_by(origin_airport_id=origin_id)
    if dest_id:
        query = query.filter_by(destination_airport_id=dest_id)
    if airline_id:
        query = query.filter_by(airline_id=airline_id)

    flights = query.order_by(Flight.scheduled_departure.asc()).limit(60).all()
    all_airports = Airport.query.filter_by(operational_status='Operational').order_by(Airport.city.asc()).all()
    all_airlines = Airline.query.order_by(Airline.name.asc()).all()

    return render_template(
        'flight_track.html',
        flights=flights,
        flight_number_query=flight_num,
        status_filter=status_filter,
        origin_id=origin_id,
        dest_id=dest_id,
        airline_id=airline_id,
        airports=all_airports,
        airlines=all_airlines
    )

@flights_bp.route('/flights/<int:flight_id>/track')
def track_flight(flight_id):
    flight = get_flight_by_id(flight_id)
    if not flight:
        abort(404)

    route_info = get_flight_route_coordinates(flight)
    timeline = get_flight_status_timeline(flight)
    history = flight.status_history.all()

    return render_template(
        'flight_track_detail.html',
        flight=flight,
        route_info=route_info,
        timeline=timeline,
        history=history
    )

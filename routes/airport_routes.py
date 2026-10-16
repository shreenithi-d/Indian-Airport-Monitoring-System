from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required
from models import Airport, HistoricalAirportStat, Flight
from extensions import db
from sqlalchemy import or_
from datetime import date

airport_bp = Blueprint('airports', __name__)

@airport_bp.route('/')
@login_required
def directory():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '').strip()
    state_filter = request.args.get('state', '').strip()
    status_filter = request.args.get('status', '').strip()
    class_filter = request.args.get('classification', '').strip()
    
    query = Airport.query
    
    if search:
        query = query.filter(
            or_(
                Airport.name.ilike(f'%{search}%'),
                Airport.city.ilike(f'%{search}%'),
                Airport.iata_code.ilike(f'%{search}%'),
                Airport.icao_code.ilike(f'%{search}%'),
                Airport.state.ilike(f'%{search}%')
            )
        )
    if state_filter:
        query = query.filter(Airport.state == state_filter)
    if status_filter:
        query = query.filter(Airport.operational_status == status_filter)
    if class_filter:
        query = query.filter(Airport.classification == class_filter)
    
    airports = query.order_by(Airport.name).paginate(page=page, per_page=per_page, error_out=False)
    
    states = db.session.query(Airport.state).distinct().order_by(Airport.state).all()
    states = [s[0] for s in states]
    
    return render_template('airport_directory.html',
        airports=airports,
        states=states,
        search=search,
        state_filter=state_filter,
        status_filter=status_filter,
        class_filter=class_filter
    )

@airport_bp.route('/<int:airport_id>')
@login_required
def detail(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    historical_stats = HistoricalAirportStat.query.filter_by(airport_id=airport_id).order_by(
        HistoricalAirportStat.reporting_year.desc()
    ).all()
    
    today = date.today()
    arrivals = Flight.query.filter_by(
        destination_airport_id=airport_id
    ).order_by(Flight.scheduled_arrival).limit(10).all()
    
    departures = Flight.query.filter_by(
        origin_airport_id=airport_id
    ).order_by(Flight.scheduled_departure).limit(10).all()
    
    return render_template('airport_details.html',
        airport=airport,
        historical_stats=historical_stats,
        arrivals=arrivals,
        departures=departures
    )

@airport_bp.route('/<int:airport_id>/history')
@login_required
def history(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    stats = HistoricalAirportStat.query.filter_by(airport_id=airport_id).order_by(
        HistoricalAirportStat.reporting_year.desc()
    ).all()
    return render_template('airport_history.html', airport=airport, stats=stats)

@airport_bp.route('/<int:airport_id>/arrivals')
@login_required
def arrivals(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    flights = Flight.query.filter_by(destination_airport_id=airport_id).order_by(
        Flight.scheduled_arrival
    ).limit(50).all()
    return render_template('arrivals.html', airport=airport, flights=flights, mode='arrivals')

@airport_bp.route('/<int:airport_id>/departures')
@login_required
def departures(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    flights = Flight.query.filter_by(origin_airport_id=airport_id).order_by(
        Flight.scheduled_departure
    ).limit(50).all()
    return render_template('departures.html', airport=airport, flights=flights, mode='departures')

# API endpoints
@airport_bp.route('/api/airports')
def api_airports():
    airports = Airport.query.filter_by(operational_status='Operational').all()
    return jsonify([a.to_dict() for a in airports])

@airport_bp.route('/api/airports/search')
def api_search():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])
    results = Airport.query.filter(
        or_(
            Airport.name.ilike(f'%{q}%'),
            Airport.city.ilike(f'%{q}%'),
            Airport.iata_code.ilike(f'%{q}%'),
            Airport.icao_code.ilike(f'%{q}%')
        )
    ).limit(10).all()
    return jsonify([a.to_dict() for a in results])

@airport_bp.route('/api/airports/<int:airport_id>')
def api_airport_detail(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    return jsonify(airport.to_dict())

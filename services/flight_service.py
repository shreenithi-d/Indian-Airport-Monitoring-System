from datetime import datetime, timedelta
from extensions import db
from models.flight import Flight, FlightStatusHistory
from models.airport import Airport
from models.airline import Airline
from models.aircraft import Aircraft
from models.audit_log import AuditLog
from services.airport_service import haversine_distance

VALID_STATUSES = [
    'Scheduled',
    'Check-in open',
    'Boarding',
    'Departed',
    'In flight',
    'Arrived',
    'Delayed',
    'Cancelled'
]

def search_flights(origin_id=None, destination_id=None, travel_date=None, cabin_class='Economy', airline_id=None, status=None, sort_by='fare', flight_number=None):
    query = Flight.query

    if origin_id:
        query = query.filter_by(origin_airport_id=origin_id)
    if destination_id:
        query = query.filter_by(destination_airport_id=destination_id)
    if airline_id:
        query = query.filter_by(airline_id=airline_id)
    if status and status != 'All':
        query = query.filter_by(status=status)
    if flight_number:
        query = query.filter(Flight.flight_number.ilike(f"%{flight_number.strip()}%"))

    if travel_date:
        if isinstance(travel_date, str):
            try:
                travel_date = datetime.strptime(travel_date, '%Y-%m-%d').date()
            except ValueError:
                travel_date = None
        if travel_date:
            start_dt = datetime.combine(travel_date, datetime.min.time())
            end_dt = datetime.combine(travel_date, datetime.max.time())
            query = query.filter(Flight.scheduled_departure >= start_dt, Flight.scheduled_departure <= end_dt)

    if sort_by == 'fare':
        query = query.order_by(Flight.base_fare.asc())
    elif sort_by == 'departure':
        query = query.order_by(Flight.scheduled_departure.asc())
    elif sort_by == 'arrival':
        query = query.order_by(Flight.scheduled_arrival.asc())
    else:
        query = query.order_by(Flight.scheduled_departure.asc())

    return query.all()

def get_flight_by_id(flight_id):
    return Flight.query.get(flight_id)

def get_flight_by_number(flight_number):
    return Flight.query.filter(Flight.flight_number.ilike(flight_number.strip())).first()

def get_departures_for_airport(airport_id, limit=20):
    now = datetime.utcnow()
    return Flight.query.filter_by(origin_airport_id=airport_id)\
        .order_by(Flight.scheduled_departure.asc())\
        .limit(limit).all()

def get_arrivals_for_airport(airport_id, limit=20):
    now = datetime.utcnow()
    return Flight.query.filter_by(destination_airport_id=airport_id)\
        .order_by(Flight.scheduled_arrival.asc())\
        .limit(limit).all()

def get_flight_route_coordinates(flight):
    """Returns origin and destination coordinates with flight metadata."""
    orig = flight.origin_airport
    dest = flight.destination_airport
    distance_km = haversine_distance(orig.latitude, orig.longitude, dest.latitude, dest.longitude)
    return {
        'origin': {
            'name': orig.name,
            'city': orig.city,
            'code': orig.iata_code or orig.icao_code,
            'lat': orig.latitude,
            'lng': orig.longitude
        },
        'destination': {
            'name': dest.name,
            'city': dest.city,
            'code': dest.iata_code or dest.icao_code,
            'lat': dest.latitude,
            'lng': dest.longitude
        },
        'distance_km': distance_km,
        'flight_number': flight.flight_number,
        'airline': flight.airline.name,
        'status': flight.status
    }

def get_flight_status_timeline(flight):
    """Returns milestone list indicating which stages have completed based on current status."""
    milestones = [
        {'key': 'Scheduled', 'label': 'Flight Scheduled', 'desc': 'Timetable published'},
        {'key': 'Check-in open', 'label': 'Check-in Open', 'desc': 'Counters & web check-in open'},
        {'key': 'Boarding', 'label': 'Boarding', 'desc': f'Gate {flight.gate or "TBD"}'},
        {'key': 'Departed', 'label': 'Departed', 'desc': 'Wheels up from origin'},
        {'key': 'In flight', 'label': 'In Flight', 'desc': 'Cruising on scheduled route'},
        {'key': 'Arrived', 'label': 'Arrived', 'desc': f'Touchdown at {flight.destination_airport.city}'}
    ]

    order_map = {m['key']: i for i, m in enumerate(milestones)}
    current_idx = order_map.get(flight.status, 0)
    is_cancelled = (flight.status == 'Cancelled')
    is_delayed = (flight.status == 'Delayed')

    timeline = []
    for i, m in enumerate(milestones):
        item = dict(m)
        if is_cancelled:
            item['state'] = 'cancelled' if i == 0 else 'upcoming'
        elif is_delayed and i <= 2:
            item['state'] = 'delayed'
        elif i < current_idx:
            item['state'] = 'completed'
        elif i == current_idx:
            item['state'] = 'active'
        else:
            item['state'] = 'upcoming'
        timeline.append(item)
    return timeline

def update_flight_status(flight_id, new_status, source='Operational Schedule', notes=None, actor_user_id=None):
    flight = Flight.query.get(flight_id)
    if not flight:
        return None, "Flight not found."
    if new_status not in VALID_STATUSES:
        return None, f"Invalid flight status '{new_status}'."

    prev_status = flight.status
    flight.status = new_status
    flight.updated_at = datetime.utcnow()

    # If departed or arrived, record actual timestamps
    if new_status == 'Departed' and not flight.actual_departure:
        flight.actual_departure = datetime.utcnow()
    elif new_status == 'Arrived' and not flight.actual_arrival:
        flight.actual_arrival = datetime.utcnow()

    history = FlightStatusHistory(
        flight_id=flight.id,
        previous_status=prev_status,
        new_status=new_status,
        source=source,
        notes=notes or f"Status changed from {prev_status} to {new_status}"
    )
    db.session.add(history)

    audit = AuditLog(
        actor_user_id=actor_user_id,
        action='UPDATE_FLIGHT_STATUS',
        entity_type='Flight',
        entity_id=flight.id,
        notes=f"Changed status of flight {flight.flight_number} to {new_status}"
    )
    db.session.add(audit)
    db.session.commit()
    return flight, "Status updated successfully."

def create_flight(data, actor_user_id=None):
    origin_id = int(data['origin_airport_id'])
    dest_id = int(data['destination_airport_id'])
    if origin_id == dest_id:
        return None, "Origin and destination airport cannot be the same."

    sched_dep = datetime.strptime(data['scheduled_departure'], '%Y-%m-%dT%H:%M')
    sched_arr = datetime.strptime(data['scheduled_arrival'], '%Y-%m-%dT%H:%M')
    if sched_arr <= sched_dep:
        return None, "Scheduled arrival must be after scheduled departure."

    flight = Flight(
        flight_number=data['flight_number'].strip().upper(),
        airline_id=int(data['airline_id']),
        aircraft_id=int(data['aircraft_id']),
        origin_airport_id=origin_id,
        destination_airport_id=dest_id,
        scheduled_departure=sched_dep,
        scheduled_arrival=sched_arr,
        base_fare=float(data.get('base_fare', 4500.0)),
        status=data.get('status', 'Scheduled'),
        terminal=data.get('terminal', 'T1'),
        gate=data.get('gate', 'G1'),
        baggage_belt=data.get('baggage_belt', 'B1'),
        data_source='Reference Schedule'
    )
    db.session.add(flight)
    db.session.flush()

    # Initial history
    history = FlightStatusHistory(
        flight_id=flight.id,
        previous_status=None,
        new_status=flight.status,
        source='Schedule Creation',
        notes='Flight schedule added to operational system.'
    )
    db.session.add(history)

    audit = AuditLog(
        actor_user_id=actor_user_id,
        action='CREATE_FLIGHT',
        entity_type='Flight',
        entity_id=flight.id,
        notes=f"Created flight {flight.flight_number}"
    )
    db.session.add(audit)
    db.session.commit()
    return flight, "Flight created successfully."

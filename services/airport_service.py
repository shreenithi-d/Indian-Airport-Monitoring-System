import math
import csv
import io
from extensions import db
from models.airport import Airport
from models.audit_log import AuditLog

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two coordinate pairs using Haversine formula."""
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)

def get_all_airports(category=None, state=None, operational_status=None, search=None):
    query = Airport.query
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            db.or_(
                Airport.name.ilike(search_term),
                Airport.city.ilike(search_term),
                Airport.state.ilike(search_term),
                Airport.iata_code.ilike(search_term),
                Airport.icao_code.ilike(search_term)
            )
        )
    if category and category != 'All':
        query = query.filter_by(category=category)
    if state and state != 'All':
        query = query.filter_by(state=state)
    if operational_status and operational_status != 'All':
        query = query.filter_by(operational_status=operational_status)
    return query.order_by(Airport.city.asc()).all()

def get_airport_by_id(airport_id):
    return Airport.query.get(airport_id)

def get_airport_by_code(code):
    if not code:
        return None
    code = code.strip().upper()
    return Airport.query.filter(
        db.or_(Airport.iata_code == code, Airport.icao_code == code)
    ).first()

def get_nearby_airports(airport, max_km=500, limit=5):
    """Find closest operational airports."""
    all_airports = Airport.query.filter(Airport.id != airport.id).all()
    distances = []
    for a in all_airports:
        dist = haversine_distance(airport.latitude, airport.longitude, a.latitude, a.longitude)
        if dist <= max_km:
            distances.append((a, dist))
    distances.sort(key=lambda x: x[1])
    return distances[:limit]

def create_airport(data, actor_user_id=None):
    airport = Airport(
        name=data['name'].strip(),
        city=data['city'].strip(),
        state=data['state'].strip(),
        iata_code=data.get('iata_code', '').strip().upper() or None,
        icao_code=data.get('icao_code', '').strip().upper() or None,
        latitude=float(data['latitude']),
        longitude=float(data['longitude']),
        category=data.get('category', 'Domestic'),
        operational_status=data.get('operational_status', 'Operational'),
        terminals=data.get('terminals', 'T1'),
        description=data.get('description', '').strip()
    )
    db.session.add(airport)
    db.session.flush()

    audit = AuditLog(
        actor_user_id=actor_user_id,
        action='CREATE_AIRPORT',
        entity_type='Airport',
        entity_id=airport.id,
        notes=f"Added airport {airport.name} ({airport.iata_code or airport.icao_code})"
    )
    db.session.add(audit)
    db.session.commit()
    return airport

def update_airport(airport, data, actor_user_id=None):
    airport.name = data.get('name', airport.name).strip()
    airport.city = data.get('city', airport.city).strip()
    airport.state = data.get('state', airport.state).strip()
    airport.iata_code = data.get('iata_code', airport.iata_code).strip().upper() or None
    airport.icao_code = data.get('icao_code', airport.icao_code).strip().upper() or None
    airport.latitude = float(data.get('latitude', airport.latitude))
    airport.longitude = float(data.get('longitude', airport.longitude))
    airport.category = data.get('category', airport.category)
    airport.operational_status = data.get('operational_status', airport.operational_status)
    airport.terminals = data.get('terminals', airport.terminals)
    airport.description = data.get('description', airport.description)

    audit = AuditLog(
        actor_user_id=actor_user_id,
        action='UPDATE_AIRPORT',
        entity_type='Airport',
        entity_id=airport.id,
        notes=f"Updated airport details for {airport.name}"
    )
    db.session.add(audit)
    db.session.commit()
    return airport

def delete_or_deactivate_airport(airport, actor_user_id=None):
    """Deactivates if historical flights exist, otherwise deletes safely."""
    has_flights = airport.departing_flights.count() > 0 or airport.arriving_flights.count() > 0
    if has_flights:
        airport.operational_status = 'Non-Operational'
        audit = AuditLog(
            actor_user_id=actor_user_id,
            action='DEACTIVATE_AIRPORT',
            entity_type='Airport',
            entity_id=airport.id,
            notes=f"Airport has dependent flights; changed status to Non-Operational."
        )
        db.session.add(audit)
        db.session.commit()
        return False, "Airport has associated flights. Marked as Non-Operational instead of permanent deletion."
    else:
        airport_id = airport.id
        airport_name = airport.name
        db.session.delete(airport)
        audit = AuditLog(
            actor_user_id=actor_user_id,
            action='DELETE_AIRPORT',
            entity_type='Airport',
            entity_id=airport_id,
            notes=f"Deleted airport {airport_name}"
        )
        db.session.add(audit)
        db.session.commit()
        return True, "Airport deleted successfully."

def import_airports_from_csv(file_stream, actor_user_id=None):
    """Import airports from uploaded CSV data with validation and transaction safety."""
    stream = io.StringIO(file_stream.read().decode("UTF8"), newline=None)
    csv_reader = csv.DictReader(stream)
    
    imported_count = 0
    skipped_count = 0
    errors = []

    for row_idx, row in enumerate(csv_reader, start=2):
        name = row.get('name', '').strip()
        city = row.get('city', '').strip()
        state = row.get('state', '').strip()
        iata_code = row.get('iata_code', '').strip().upper() or None
        icao_code = row.get('icao_code', '').strip().upper() or None
        lat_val = row.get('latitude', '').strip()
        lon_val = row.get('longitude', '').strip()
        category = row.get('category', 'Domestic').strip()
        status = row.get('operational_status', 'Operational').strip()
        terminals = row.get('terminals', 'T1').strip()
        desc = row.get('description', '').strip()

        if not name or not city or not state:
            errors.append(f"Row {row_idx}: Missing required name/city/state.")
            skipped_count += 1
            continue

        try:
            lat = float(lat_val)
            lon = float(lon_val)
            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError("Out of bounds")
        except (ValueError, TypeError):
            errors.append(f"Row {row_idx}: Invalid coordinates '{lat_val}', '{lon_val}'.")
            skipped_count += 1
            continue

        # Check existing
        existing = None
        if iata_code:
            existing = Airport.query.filter_by(iata_code=iata_code).first()
        elif icao_code:
            existing = Airport.query.filter_by(icao_code=icao_code).first()
        
        if existing:
            skipped_count += 1
            continue

        airport = Airport(
            name=name,
            city=city,
            state=state,
            iata_code=iata_code,
            icao_code=icao_code,
            latitude=lat,
            longitude=lon,
            category=category,
            operational_status=status,
            terminals=terminals,
            description=desc
        )
        db.session.add(airport)
        imported_count += 1

    if imported_count > 0:
        audit = AuditLog(
            actor_user_id=actor_user_id,
            action='IMPORT_AIRPORTS_CSV',
            entity_type='Airport',
            notes=f"CSV import: {imported_count} imported, {skipped_count} skipped."
        )
        db.session.add(audit)
        db.session.commit()

    return {
        'imported': imported_count,
        'skipped': skipped_count,
        'errors': errors
    }

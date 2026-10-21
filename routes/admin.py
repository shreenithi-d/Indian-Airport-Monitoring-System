from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import datetime
from extensions import db
from models.user import User
from models.airport import Airport
from models.airline import Airline
from models.aircraft import Aircraft, AircraftSeat
from models.flight import Flight, FlightStatusHistory
from models.booking import Booking, SeatReservation
from models.audit_log import AuditLog
from utils.permissions import admin_required
from services.airport_service import (
    create_airport,
    update_airport,
    delete_or_deactivate_airport,
    import_airports_from_csv
)
from services.flight_service import (
    create_flight,
    update_flight_status
)
from services.booking_service import cancel_booking_transaction

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_airports = Airport.query.count()
    total_flights = Flight.query.count()
    active_bookings = Booking.query.filter_by(booking_status='Confirmed').count()
    cancelled_bookings = Booking.query.filter_by(booking_status='Cancelled').count()
    total_passengers = User.query.filter_by(role='passenger').count()
    total_aircraft = Aircraft.query.count()
    delayed_flights = Flight.query.filter_by(status='Delayed').count()
    total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter_by(booking_status='Confirmed').scalar() or 0.0
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(6).all()
    # Recent audit logs
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    
    stats = {
        'total_airports': total_airports,
        'total_flights': total_flights,
        'active_bookings': f"{active_bookings:,}",
        'cancelled_bookings': f"{cancelled_bookings:,}",
        'total_passengers': f"{total_passengers:,}",
        'total_aircraft': total_aircraft,
        'delayed_flights': delayed_flights,
        'total_revenue': round(total_revenue, 2)
    }

    return render_template('admin/dashboard.html', stats=stats, recent_bookings=recent_bookings, recent_logs=recent_logs)

# --- Airport Management ---
@admin_bp.route('/airports')
@admin_required
def airports():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', 'All')
    page = request.args.get('page', 1, type=int)

    query = Airport.query
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Airport.name.ilike(search_term),
                Airport.city.ilike(search_term),
                Airport.iata_code.ilike(search_term)
            )
        )
    if category != 'All':
        query = query.filter_by(category=category)

    pagination = query.order_by(Airport.name.asc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/airports.html', pagination=pagination, airports=pagination.items, search=search, category=category)

@admin_bp.route('/airports/add', methods=['GET', 'POST'])
@admin_required
def add_airport():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        iata = request.form.get('iata_code', '').strip().upper() or None
        icao = request.form.get('icao_code', '').strip().upper() or None
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        category = request.form.get('category', 'Domestic')
        status = request.form.get('operational_status', 'Operational')
        terminals = request.form.get('terminals', 'T1')
        desc = request.form.get('description', '')

        if not name or not city or not state or not lat or not lon:
            flash("Please fill in all mandatory fields.", "danger")
            return render_template('admin/airport_form.html', airport=None)

        try:
            airport = create_airport({
                'name': name,
                'city': city,
                'state': state,
                'iata_code': iata,
                'icao_code': icao,
                'latitude': lat,
                'longitude': lon,
                'category': category,
                'operational_status': status,
                'terminals': terminals,
                'description': desc
            })
            flash(f"Airport '{airport.name}' added successfully.", "success")
            return redirect(url_for('admin.airports'))
        except Exception as e:
            flash(f"Failed to create airport: {str(e)}", "danger")

    return render_template('admin/airport_form.html', airport=None)

@admin_bp.route('/airports/<int:airport_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_airport(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    if request.method == 'POST':
        try:
            update_airport(airport, {
                'name': request.form.get('name'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'iata_code': request.form.get('iata_code'),
                'icao_code': request.form.get('icao_code'),
                'latitude': request.form.get('latitude'),
                'longitude': request.form.get('longitude'),
                'category': request.form.get('category'),
                'operational_status': request.form.get('operational_status'),
                'terminals': request.form.get('terminals'),
                'description': request.form.get('description')
            })
            flash(f"Airport '{airport.name}' updated successfully.", "success")
            return redirect(url_for('admin.airports'))
        except Exception as e:
            flash(f"Update failed: {str(e)}", "danger")

    return render_template('admin/airport_form.html', airport=airport)

@admin_bp.route('/airports/<int:airport_id>/delete', methods=['POST'])
@admin_required
def delete_airport(airport_id):
    airport = Airport.query.get_or_404(airport_id)
    deleted, msg = delete_or_deactivate_airport(airport)
    flash(msg, "success" if deleted else "warning")
    return redirect(url_for('admin.airports'))

@admin_bp.route('/airports/import-csv', methods=['POST'])
@admin_required
def import_csv():
    if 'csv_file' not in request.files:
        flash("No file part provided.", "danger")
        return redirect(url_for('admin.airports'))
    
    file = request.files['csv_file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for('admin.airports'))

    if not file.filename.endswith('.csv'):
        flash("Please upload a valid CSV file.", "danger")
        return redirect(url_for('admin.airports'))

    res = import_airports_from_csv(file)
    flash(f"CSV Import Result: {res['imported']} airports added, {res['skipped']} skipped.", "info")
    if res['errors']:
        for err in res['errors'][:5]:
            flash(err, "warning")
    return redirect(url_for('admin.airports'))

# --- Flight Management ---
@admin_bp.route('/flights')
@admin_required
def flights():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'All')
    origin_id = request.args.get('origin_id', type=int)
    dest_id = request.args.get('dest_id', type=int)
    airline_id = request.args.get('airline_id', type=int)
    page = request.args.get('page', 1, type=int)

    query = Flight.query
    if search:
        query = query.filter(Flight.flight_number.ilike(f"%{search}%"))
    if status != 'All':
        query = query.filter_by(status=status)
    if origin_id:
        query = query.filter_by(origin_airport_id=origin_id)
    if dest_id:
        query = query.filter_by(destination_airport_id=dest_id)
    if airline_id:
        query = query.filter_by(airline_id=airline_id)

    pagination = query.order_by(Flight.scheduled_departure.desc()).paginate(page=page, per_page=15, error_out=False)
    
    all_airports = Airport.query.filter_by(operational_status='Operational').order_by(Airport.city.asc()).all()
    all_airlines = Airline.query.order_by(Airline.name.asc()).all()

    return render_template(
        'admin/flights.html',
        pagination=pagination,
        flights=pagination.items,
        search=search,
        status=status,
        origin_id=origin_id,
        dest_id=dest_id,
        airline_id=airline_id,
        airports=all_airports,
        airlines=all_airlines
    )

@admin_bp.route('/flights/<int:flight_id>')
@admin_required
def flight_detail(flight_id):
    from services.seat_service import get_flight_seat_map
    flight = Flight.query.get_or_404(flight_id)
    
    # Get passengers and seat reservations for this flight
    reservations = SeatReservation.query.filter_by(flight_id=flight.id).all()
    
    # Manifest data
    manifest = []
    male_count = 0
    female_count = 0
    other_count = 0
    total_revenue = 0.0
    confirmed_seats = 0
    cancelled_seats = 0

    for r in reservations:
        pax = r.passenger
        booking = r.booking
        status = r.reservation_status
        if status == 'Confirmed':
            confirmed_seats += 1
            if pax:
                if pax.gender_selection == 'Male':
                    male_count += 1
                elif pax.gender_selection == 'Female':
                    female_count += 1
                else:
                    other_count += 1
            if booking:
                # Share of booking total
                per_pax_fare = (booking.total_amount / max(1, booking.passenger_count))
                total_revenue += per_pax_fare
        elif status == 'Cancelled':
            cancelled_seats += 1

        manifest.append({
            'reservation_id': r.id,
            'seat_code': r.seat.seat_code if r.seat else (pax.seat_number if pax else '—'),
            'cabin_class': r.seat.cabin_class if r.seat else 'Economy',
            'passenger_name': pax.full_name if pax else 'Unknown',
            'gender': pax.gender_selection if pax else 'Prefer not to say',
            'age': pax.age if pax else '—',
            'booking_ref': booking.booking_reference if booking else '—',
            'booking_id': booking.id if booking else None,
            'user_email': booking.user.email if (booking and booking.user) else '—',
            'status': status,
            'fare': round((booking.total_amount / max(1, booking.passenger_count)), 2) if booking else flight.base_fare
        })

    # Sort manifest by seat code
    manifest.sort(key=lambda x: (x['seat_code'][:2].isdigit(), int(x['seat_code'][:-1]) if x['seat_code'][:-1].isdigit() else 999, x['seat_code'][-1:]))

    total_capacity = flight.aircraft.seat_capacity if flight.aircraft else 180
    occupancy_pct = round((confirmed_seats / max(1, total_capacity)) * 100, 1)

    seat_map_data = get_flight_seat_map(flight.id)
    history = flight.status_history.all()

    stats = {
        'total_capacity': total_capacity,
        'confirmed_seats': confirmed_seats,
        'available_seats': max(0, total_capacity - confirmed_seats),
        'cancelled_seats': cancelled_seats,
        'occupancy_pct': occupancy_pct,
        'total_revenue': round(total_revenue, 2),
        'male_count': male_count,
        'female_count': female_count,
        'other_count': other_count
    }

    return render_template(
        'admin/flight_detail.html',
        flight=flight,
        manifest=manifest,
        stats=stats,
        seat_map=seat_map_data,
        history=history
    )

@admin_bp.route('/flights/add', methods=['GET', 'POST'])
@admin_required
def add_flight():
    airports = Airport.query.filter_by(operational_status='Operational').order_by(Airport.city.asc()).all()
    airlines = Airline.query.order_by(Airline.name.asc()).all()
    aircraft = Aircraft.query.filter_by(active_status=True).all()

    if request.method == 'POST':
        flight, msg = create_flight(request.form)
        if flight:
            flash(f"Flight {flight.flight_number} created successfully.", "success")
            return redirect(url_for('admin.flights'))
        else:
            flash(msg, "danger")

    return render_template('admin/flight_form.html', airports=airports, airlines=airlines, aircraft_list=aircraft)

@admin_bp.route('/flights/<int:flight_id>/status', methods=['POST'])
@admin_required
def update_status(flight_id):
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    flight, msg = update_flight_status(flight_id, new_status, source='Admin Manual Update', notes=notes)
    if flight:
        flash(f"Status for {flight.flight_number} updated to '{new_status}'.", "success")
    else:
        flash(msg, "danger")
    
    # Check redirect destination
    redirect_to = request.form.get('redirect_to')
    if redirect_to == 'detail':
        return redirect(url_for('admin.flight_detail', flight_id=flight_id))
    return redirect(url_for('admin.flights'))

@admin_bp.route('/flights/<int:flight_id>/operations', methods=['POST'])
@admin_required
def update_operations(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    terminal = request.form.get('terminal', flight.terminal).strip()
    gate = request.form.get('gate', flight.gate).strip()
    baggage_belt = request.form.get('baggage_belt', flight.baggage_belt).strip()
    
    old_details = f"T:{flight.terminal}, G:{flight.gate}, B:{flight.baggage_belt}"
    flight.terminal = terminal
    flight.gate = gate
    flight.baggage_belt = baggage_belt
    flight.updated_at = datetime.utcnow()
    
    audit = AuditLog(
        action='UPDATE_FLIGHT_OPERATIONS',
        entity_type='Flight',
        entity_id=flight.id,
        notes=f"Updated flight {flight.flight_number} operations from ({old_details}) to (T:{terminal}, G:{gate}, B:{baggage_belt})"
    )
    db.session.add(audit)
    db.session.commit()
    flash(f"Flight {flight.flight_number} operational allocations updated successfully.", "success")
    return redirect(url_for('admin.flight_detail', flight_id=flight_id))

# --- Aircraft & Fleet ---
@admin_bp.route('/aircraft')
@admin_required
def fleet():
    aircraft_list = Aircraft.query.order_by(Aircraft.model.asc()).all()
    return render_template('admin/aircraft.html', aircraft_list=aircraft_list)

@admin_bp.route('/aircraft/<int:aircraft_id>/seats')
@admin_required
def seat_management(aircraft_id):
    aircraft = Aircraft.query.get_or_404(aircraft_id)
    seats = aircraft.seats.order_by(AircraftSeat.row_number.asc(), AircraftSeat.seat_letter.asc()).all()
    return render_template('admin/seat_management.html', aircraft=aircraft, seats=seats)

# --- Booking Management ---
@admin_bp.route('/bookings')
@admin_required
def bookings():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', 'All')
    page = request.args.get('page', 1, type=int)

    query = Booking.query
    if search:
        query = query.filter(Booking.booking_reference.ilike(f"%{search}%"))
    if status != 'All':
        query = query.filter_by(booking_status=status)

    pagination = query.order_by(Booking.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/bookings.html', pagination=pagination, bookings=pagination.items, search=search, status=status)

@admin_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@admin_required
def cancel_booking_admin(booking_id):
    reason = request.form.get('reason', 'Cancelled by administrator')
    success, msg = cancel_booking_transaction(booking_id=booking_id, is_admin=True, reason=reason)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('admin.bookings'))

# --- Passenger & User Management ---
@admin_bp.route('/users')
@admin_required
def users():
    search = request.args.get('search', '').strip()
    role = request.args.get('role', 'All')
    page = request.args.get('page', 1, type=int)

    query = User.query
    if search:
        search_term = f"%{search}%"
        query = query.filter(db.or_(User.full_name.ilike(search_term), User.email.ilike(search_term)))
    if role != 'All':
        query = query.filter_by(role=role)

    pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/users.html', pagination=pagination, users=pagination.items, search=search, role=role)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash("Cannot modify status of an administrator account.", "danger")
        return redirect(url_for('admin.users'))

    user.account_status = 'suspended' if user.account_status == 'active' else 'active'
    audit = AuditLog(
        action='TOGGLE_USER_STATUS',
        entity_type='User',
        entity_id=user.id,
        notes=f"Changed account status of {user.email} to {user.account_status}"
    )
    db.session.add(audit)
    db.session.commit()
    flash(f"User {user.email} status changed to '{user.account_status}'.", "info")
    return redirect(url_for('admin.users'))

# --- Analytics ---
@admin_bp.route('/analytics')
@admin_required
def analytics():
    # Calculated statistics for operational reports
    total_airports = Airport.query.count()
    category_counts = db.session.query(Airport.category, db.func.count(Airport.id))\
        .group_by(Airport.category).all()
    status_counts = db.session.query(Flight.status, db.func.count(Flight.id))\
        .group_by(Flight.status).all()
    booking_status_counts = db.session.query(Booking.booking_status, db.func.count(Booking.id))\
        .group_by(Booking.booking_status).all()

    return render_template(
        'admin/analytics.html',
        category_counts=category_counts,
        status_counts=status_counts,
        booking_status_counts=booking_status_counts,
        total_airports=total_airports
    )

# --- Audit Logs & Settings ---
@admin_bp.route('/audit-logs')
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    pagination = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/audit_logs.html', pagination=pagination, logs=pagination.items)

@admin_bp.route('/settings')
@admin_required
def settings():
    return render_template('admin/settings.html')

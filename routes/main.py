from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.airport import Airport
from models.flight import Flight
from models.booking import Booking
from models.notification import Notification

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    # Live database statistics
    total_airports = Airport.query.count()
    total_flights = Flight.query.count()
    total_departures = Flight.query.filter(Flight.status.in_(['Departed', 'In flight', 'Arrived'])).count()
    total_bookings = Booking.query.filter_by(booking_status='Confirmed').count()
    delayed_flights = Flight.query.filter_by(status='Delayed').count()

    # Featured airports for discovery section
    featured_codes = ['DEL', 'BOM', 'BLR', 'HYD', 'CCU', 'MAA', 'COK', 'JAI']
    featured_airports = Airport.query.filter(Airport.iata_code.in_(featured_codes)).all()

    # All airports for quick flight search dropdown
    all_airports = Airport.query.filter_by(operational_status='Operational').order_by(Airport.city.asc()).all()

    stats = {
        'total_airports': total_airports,
        'total_flights': total_flights,
        'total_departures': total_departures,
        'total_bookings': total_bookings,
        'delayed_flights': delayed_flights
    }

    return render_template(
        'landing.html',
        stats=stats,
        featured_airports=featured_airports,
        airports=all_airports
    )

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/notifications')
@login_required
def notifications():
    user_notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=user_notifications)

@main_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for('main.notifications'))

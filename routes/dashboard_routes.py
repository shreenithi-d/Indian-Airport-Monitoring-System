from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Airport, Flight, Booking, User
from datetime import datetime, timezone
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Summary stats
    total_airports = Airport.query.count()
    operational_airports = Airport.query.filter_by(operational_status='Operational').count()
    international_airports = Airport.query.filter_by(classification='International').count()
    
    # User's bookings
    user_bookings_count = Booking.query.filter_by(user_id=current_user.id).count()
    
    # Recent airports (for quick access)
    recent_airports = Airport.query.filter_by(operational_status='Operational').order_by(Airport.name).limit(8).all()
    
    # States
    states = db.session.query(Airport.state).distinct().order_by(Airport.state).all()
    states = [s[0] for s in states]
    
    now = datetime.now(timezone.utc)
    
    return render_template('dashboard.html',
        total_airports=total_airports,
        operational_airports=operational_airports,
        international_airports=international_airports,
        user_bookings_count=user_bookings_count,
        recent_airports=recent_airports,
        states=states,
        now=now
    )

from routes.auth import auth_bp
from routes.main import main_bp
from routes.airports import airports_bp
from routes.flights import flights_bp
from routes.seats import seats_bp
from routes.bookings import bookings_bp
from routes.admin import admin_bp
from routes.api import api_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'airports_bp',
    'flights_bp',
    'seats_bp',
    'bookings_bp',
    'admin_bp',
    'api_bp'
]

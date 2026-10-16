from flask import Flask, render_template
from config import Config
from extensions import db, login_manager, csrf
from models.user import User
from models.notification import Notification

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Exclude API endpoints from CSRF if needed for purely GET/read requests (POST/state changes still protected)
    # Register blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.airports import airports_bp
    from routes.flights import flights_bp
    from routes.seats import seats_bp
    from routes.bookings import bookings_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(airports_bp)
    app.register_blueprint(flights_bp)
    app.register_blueprint(seats_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Custom Jinja Filters
    @app.template_filter('currency')
    def currency_filter(val):
        try:
            return f"₹{float(val):,.2f}"
        except (ValueError, TypeError):
            return f"₹{val}"

    @app.template_filter('datetime')
    def datetime_filter(dt, format='%d %b %Y, %I:%M %p'):
        if not dt:
            return 'N/A'
        return dt.strftime(format)

    @app.template_filter('date')
    def date_filter(dt, format='%d %b %Y'):
        if not dt:
            return 'N/A'
        return dt.strftime(format)

    @app.template_filter('time')
    def time_filter(dt, format='%I:%M %p'):
        if not dt:
            return 'N/A'
        return dt.strftime(format)

    # Context Processors
    @app.context_processor
    def inject_global_data():
        from flask_login import current_user
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {
            'app_name': app.config.get('APP_NAME', 'Indian Airport Monitoring System'),
            'app_tagline': app.config.get('APP_TAGLINE', 'Smart Airport Map, Flight Tracking and Ticket Booking'),
            'demo_mode': app.config.get('DEMO_MODE', True),
            'unread_notifications_count': unread_count
        }

    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Auto seed reference data on first run if database is fresh
    with app.app_context():
        db.create_all()
        from models.airport import Airport
        if Airport.query.count() == 0 and not app.config.get('TESTING'):
            from seed import seed_database
            seed_database(app)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)

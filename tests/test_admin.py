from models.airport import Airport
from models.flight import Flight
from models.audit_log import AuditLog
from services.airport_service import create_airport, update_airport
from services.flight_service import update_flight_status

def test_admin_airport_crud_and_audit(app):
    with app.app_context():
        # Create Airport
        apt = create_airport({
            'name': 'Jaipur Sanganer Airport',
            'city': 'Jaipur',
            'state': 'Rajasthan',
            'iata_code': 'JAI',
            'icao_code': 'VIJP',
            'latitude': 26.8242,
            'longitude': 75.8122,
            'category': 'International',
            'operational_status': 'Operational',
            'terminals': 'T1, T2',
            'description': 'Pink City Hub'
        }, actor_user_id=1)

        assert apt.id is not None
        assert apt.iata_code == 'JAI'

        # Check Audit Log created
        audit = AuditLog.query.filter_by(action='CREATE_AIRPORT', entity_id=apt.id).first()
        assert audit is not None
        assert "Jaipur" in audit.notes

        # Update Airport
        update_airport(apt, {
            'name': 'Jaipur International Airport',
            'city': 'Jaipur',
            'state': 'Rajasthan',
            'latitude': 26.8242,
            'longitude': 75.8122,
            'category': 'International',
            'operational_status': 'Operational',
            'terminals': 'T1, T2 (Expanded)'
        }, actor_user_id=1)

        assert apt.terminals == 'T1, T2 (Expanded)'
        update_audit = AuditLog.query.filter_by(action='UPDATE_AIRPORT', entity_id=apt.id).first()
        assert update_audit is not None

def test_admin_flight_status_update_and_audit(app):
    with app.app_context():
        flight = Flight.query.first()
        updated, msg = update_flight_status(flight.id, 'Delayed', notes="Monsoon weather delay", actor_user_id=1)
        assert updated.status == 'Delayed'

        audit = AuditLog.query.filter_by(action='UPDATE_FLIGHT_STATUS', entity_id=flight.id).first()
        assert audit is not None
        assert "Delayed" in audit.notes

def test_admin_analytics_api_endpoint(client):
    # Log in as admin
    client.post('/login', data={'email': 'admin@test.com', 'password': 'Admin@123'})
    
    response = client.get('/api/analytics/charts')
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'categories' in json_data
    assert 'flight_statuses' in json_data
    assert 'booking_statuses' in json_data

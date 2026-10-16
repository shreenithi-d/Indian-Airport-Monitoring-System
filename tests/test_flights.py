from datetime import datetime, timedelta
from models.flight import Flight
from models.airport import Airport
from models.airline import Airline
from models.aircraft import Aircraft
from services.flight_service import (
    search_flights,
    get_flight_by_id,
    create_flight,
    update_flight_status,
    get_flight_status_timeline
)

def test_flight_search_and_filter(app):
    with app.app_context():
        del_apt = Airport.query.filter_by(iata_code='DEL').first()
        bom_apt = Airport.query.filter_by(iata_code='BOM').first()

        flights = search_flights(origin_id=del_apt.id, destination_id=bom_apt.id)
        assert len(flights) >= 1
        assert flights[0].flight_number == 'AI-TEST1'

def test_flight_creation_invalid_origin_dest(app):
    with app.app_context():
        del_apt = Airport.query.filter_by(iata_code='DEL').first()
        airline = Airline.query.first()
        aircraft = Aircraft.query.first()

        flight, msg = create_flight({
            'flight_number': 'ERR-101',
            'airline_id': airline.id,
            'aircraft_id': aircraft.id,
            'origin_airport_id': del_apt.id,
            'destination_airport_id': del_apt.id,  # Same airport!
            'scheduled_departure': '2026-10-20T10:00',
            'scheduled_arrival': '2026-10-20T12:00',
            'base_fare': 5000.0
        })
        assert flight is None
        assert "cannot be the same" in msg

def test_flight_status_update_and_history(app):
    with app.app_context():
        flight = Flight.query.filter_by(flight_number='AI-TEST1').first()
        assert flight.status == 'Scheduled'

        # Update status to Boarding
        updated, msg = update_flight_status(flight.id, 'Boarding', notes="Gate boarding initiated")
        assert updated is not None
        assert updated.status == 'Boarding'

        # Check status history was logged
        history = flight.status_history.first()
        assert history is not None
        assert history.new_status == 'Boarding'
        assert history.previous_status == 'Scheduled'

        # Verify milestone timeline
        timeline = get_flight_status_timeline(flight)
        boarding_step = next(item for item in timeline if item['key'] == 'Boarding')
        assert boarding_step['state'] == 'active'

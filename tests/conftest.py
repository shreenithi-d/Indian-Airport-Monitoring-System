import pytest
from datetime import datetime, timedelta
from app import create_app
from config import TestConfig
from extensions import db
from models.user import User
from models.airport import Airport
from models.airline import Airline
from models.aircraft import Aircraft, AircraftSeat
from models.flight import Flight
from services.seat_service import generate_aircraft_seats

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

        # Seed Test Admin
        admin = User(
            full_name="Admin Test",
            email="admin@test.com",
            phone_number="+91 99999 88888",
            role="admin",
            account_status="active"
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        # Seed Test Passenger
        passenger = User(
            full_name="Passenger Test",
            email="passenger@test.com",
            phone_number="+91 77777 66666",
            role="passenger",
            account_status="active"
        )
        passenger.set_password("Pass@123")
        db.session.add(passenger)

        # Seed Test Airports (DEL & BOM)
        del_apt = Airport(
            name="Indira Gandhi International Airport",
            city="New Delhi",
            state="Delhi",
            iata_code="DEL",
            icao_code="VIDP",
            latitude=28.5562,
            longitude=77.1000,
            category="International",
            operational_status="Operational",
            terminals="T1, T2, T3",
            description="Delhi Hub"
        )
        bom_apt = Airport(
            name="Chhatrapati Shivaji Maharaj International Airport",
            city="Mumbai",
            state="Maharashtra",
            iata_code="BOM",
            icao_code="VABB",
            latitude=19.0896,
            longitude=72.8656,
            category="International",
            operational_status="Operational",
            terminals="T1, T2",
            description="Mumbai Hub"
        )
        db.session.add_all([del_apt, bom_apt])
        db.session.flush()

        # Seed Airline
        airline = Airline(
            name="Air India",
            code="AI",
            callsign="AIRINDIA",
            logo_color="#E50914"
        )
        db.session.add(airline)
        db.session.flush()

        # Seed Aircraft
        aircraft = Aircraft(
            model="Airbus A320neo",
            registration="VT-TST",
            seat_capacity=180,
            layout_configuration="3-3",
            total_rows=30,
            active_status=True
        )
        db.session.add(aircraft)
        db.session.flush()

        # Generate seats for aircraft
        generate_aircraft_seats(aircraft.id)

        # Seed Flight DEL -> BOM
        now = datetime.utcnow()
        flight = Flight(
            flight_number="AI-TEST1",
            airline_id=airline.id,
            aircraft_id=aircraft.id,
            origin_airport_id=del_apt.id,
            destination_airport_id=bom_apt.id,
            scheduled_departure=now + timedelta(hours=3),
            scheduled_arrival=now + timedelta(hours=5),
            base_fare=4000.0,
            status="Scheduled",
            terminal="T3",
            gate="G1"
        )
        db.session.add(flight)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

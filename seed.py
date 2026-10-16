from datetime import datetime, timedelta
import os
from extensions import db
from models.user import User
from models.airport import Airport
from models.airline import Airline
from models.aircraft import Aircraft, AircraftSeat
from models.flight import Flight, FlightStatusHistory
from models.booking import Booking, Passenger, SeatReservation
from models.notification import Notification
from models.audit_log import AuditLog
from data.airports_data import INDIAN_AIRPORTS
from services.seat_service import generate_aircraft_seats

def seed_database(app):
    with app.app_context():
        print("Starting database initialization and seeding...")
        db.create_all()

        # 1. Seed Users
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@airportmonitor.in')
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'Admin@123456')
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                full_name="System Administrator",
                email=admin_email,
                phone_number="+91 98765 43210",
                role="admin",
                account_status="active"
            )
            admin_user.set_password(admin_pass)
            db.session.add(admin_user)
            print(f"Created Administrator account: {admin_email}")

        demo_passenger = User.query.filter_by(email='passenger@demo.in').first()
        if not demo_passenger:
            demo_passenger = User(
                full_name="Rahul Verma",
                email="passenger@demo.in",
                phone_number="+91 98111 22334",
                role="passenger",
                account_status="active"
            )
            demo_passenger.set_password("Pass@123456")
            db.session.add(demo_passenger)
            print("Created Demo Passenger account: passenger@demo.in")

        demo_passenger2 = User.query.filter_by(email='priya.sharma@demo.in').first()
        if not demo_passenger2:
            demo_passenger2 = User(
                full_name="Priya Sharma",
                email="priya.sharma@demo.in",
                phone_number="+91 98222 33445",
                role="passenger",
                account_status="active"
            )
            demo_passenger2.set_password("Pass@123456")
            db.session.add(demo_passenger2)

        db.session.commit()

        # 2. Seed Airports (110 Verified Indian Airports)
        airports_count = Airport.query.count()
        if airports_count < len(INDIAN_AIRPORTS):
            print(f"Seeding {len(INDIAN_AIRPORTS)} verified Indian airports...")
            for a_data in INDIAN_AIRPORTS:
                existing = None
                if a_data.get('iata_code'):
                    existing = Airport.query.filter_by(iata_code=a_data['iata_code']).first()
                elif a_data.get('icao_code'):
                    existing = Airport.query.filter_by(icao_code=a_data['icao_code']).first()

                if not existing:
                    airport = Airport(
                        name=a_data['name'],
                        city=a_data['city'],
                        state=a_data['state'],
                        iata_code=a_data.get('iata_code'),
                        icao_code=a_data.get('icao_code'),
                        latitude=a_data['latitude'],
                        longitude=a_data['longitude'],
                        category=a_data.get('category', 'Domestic'),
                        operational_status=a_data.get('operational_status', 'Operational'),
                        terminals=a_data.get('terminals', 'T1'),
                        description=a_data.get('description', '')
                    )
                    db.session.add(airport)
            db.session.commit()
            print(f"Airports seeded. Total now: {Airport.query.count()}")
        else:
            print(f"Airports already seeded ({airports_count} present).")

        # 3. Seed Airlines
        airlines_data = [
            {"name": "Air India", "code": "AI", "callsign": "AIRINDIA", "logo_color": "#E50914", "description": "National flag carrier airline of India."},
            {"name": "IndiGo", "code": "6E", "callsign": "IFLY", "logo_color": "#004F9E", "description": "Largest passenger airline in India by fleet & passengers."},
            {"name": "SpiceJet", "code": "SG", "callsign": "SPICEJET", "logo_color": "#FF6600", "description": "Prominent low-cost Indian carrier."},
            {"name": "Vistara", "code": "UK", "callsign": "VISTARA", "logo_color": "#581845", "description": "Full-service joint venture carrier."},
            {"name": "Akasa Air", "code": "QP", "callsign": "AKASA", "logo_color": "#FF5E00", "description": "Modern ultra low-cost Indian carrier."},
            {"name": "Alliance Air", "code": "9I", "callsign": "ALLIANCE", "logo_color": "#003366", "description": "Regional connectivity airline under UDAN."}
        ]

        airline_map = {}
        for a_data in airlines_data:
            al = Airline.query.filter_by(code=a_data['code']).first()
            if not al:
                al = Airline(**a_data)
                db.session.add(al)
                db.session.flush()
            airline_map[a_data['code']] = al
        db.session.commit()

        # 4. Seed Aircraft & Seat Maps
        aircraft_configs = [
            {"model": "Airbus A320neo", "registration": "VT-EXA", "seat_capacity": 180, "layout_configuration": "3-3", "total_rows": 30},
            {"model": "Airbus A321neo", "registration": "VT-IFJ", "seat_capacity": 180, "layout_configuration": "3-3", "total_rows": 30},
            {"model": "Boeing 737-800", "registration": "VT-SGZ", "seat_capacity": 180, "layout_configuration": "3-3", "total_rows": 30},
            {"model": "ATR 72-600", "registration": "VT-AAK", "seat_capacity": 72, "layout_configuration": "2-2", "total_rows": 18}
        ]

        aircraft_map = {}
        for ac_data in aircraft_configs:
            ac = Aircraft.query.filter_by(registration=ac_data['registration']).first()
            if not ac:
                ac = Aircraft(**ac_data)
                db.session.add(ac)
                db.session.flush()
                # Generate seats
                generate_aircraft_seats(ac.id)
            aircraft_map[ac_data['registration']] = ac
        db.session.commit()

        # 5. Seed Scheduled Flights
        if Flight.query.count() == 0:
            print("Seeding scheduled flight routes across Indian airports...")
            del_apt = Airport.query.filter_by(iata_code='DEL').first()
            bom_apt = Airport.query.filter_by(iata_code='BOM').first()
            blr_apt = Airport.query.filter_by(iata_code='BLR').first()
            hyd_apt = Airport.query.filter_by(iata_code='HYD').first()
            maa_apt = Airport.query.filter_by(iata_code='MAA').first()
            ccu_apt = Airport.query.filter_by(iata_code='CCU').first()
            cok_apt = Airport.query.filter_by(iata_code='COK').first()
            goi_apt = Airport.query.filter_by(iata_code='GOI').first()
            jai_apt = Airport.query.filter_by(iata_code='JAI').first()
            sxr_apt = Airport.query.filter_by(iata_code='SXR').first()
            vtz_apt = Airport.query.filter_by(iata_code='VTZ').first()
            gau_apt = Airport.query.filter_by(iata_code='GAU').first()
            ixc_apt = Airport.query.filter_by(iata_code='IXC').first()
            lko_apt = Airport.query.filter_by(iata_code='LKO').first()
            amd_apt = Airport.query.filter_by(iata_code='AMD').first()

            now = datetime.utcnow()
            today_date = now.date()

            sample_flights_def = [
                # Flight 1: DEL -> BOM
                {
                    "flight_number": "AI-101",
                    "airline": airline_map['AI'],
                    "aircraft": aircraft_map['VT-EXA'],
                    "origin": del_apt,
                    "dest": bom_apt,
                    "dep_offset_h": 2,
                    "duration_m": 130,
                    "base_fare": 4850.0,
                    "status": "Boarding",
                    "terminal": "T3",
                    "gate": "G12",
                    "belt": "B4"
                },
                # Flight 2: BOM -> DEL
                {
                    "flight_number": "6E-204",
                    "airline": airline_map['6E'],
                    "aircraft": aircraft_map['VT-IFJ'],
                    "origin": bom_apt,
                    "dest": del_apt,
                    "dep_offset_h": 4,
                    "duration_m": 125,
                    "base_fare": 4200.0,
                    "status": "Scheduled",
                    "terminal": "T2",
                    "gate": "G4",
                    "belt": "B2"
                },
                # Flight 3: DEL -> BLR
                {
                    "flight_number": "UK-812",
                    "airline": airline_map['UK'],
                    "aircraft": aircraft_map['VT-EXA'],
                    "origin": del_apt,
                    "dest": blr_apt,
                    "dep_offset_h": 6,
                    "duration_m": 165,
                    "base_fare": 5400.0,
                    "status": "Check-in open",
                    "terminal": "T3",
                    "gate": "G18",
                    "belt": "B5"
                },
                # Flight 4: BLR -> DEL
                {
                    "flight_number": "AI-505",
                    "airline": airline_map['AI'],
                    "aircraft": aircraft_map['VT-EXA'],
                    "origin": blr_apt,
                    "dest": del_apt,
                    "dep_offset_h": 8,
                    "duration_m": 160,
                    "base_fare": 5250.0,
                    "status": "Scheduled",
                    "terminal": "T2",
                    "gate": "G8",
                    "belt": "B3"
                },
                # Flight 5: DEL -> HYD
                {
                    "flight_number": "6E-651",
                    "airline": airline_map['6E'],
                    "aircraft": aircraft_map['VT-IFJ'],
                    "origin": del_apt,
                    "dest": hyd_apt,
                    "dep_offset_h": 10,
                    "duration_m": 135,
                    "base_fare": 4100.0,
                    "status": "Scheduled",
                    "terminal": "T1",
                    "gate": "G2",
                    "belt": "B1"
                },
                # Flight 6: BOM -> BLR
                {
                    "flight_number": "QP-1102",
                    "airline": airline_map['QP'],
                    "aircraft": aircraft_map['VT-SGZ'],
                    "origin": bom_apt,
                    "dest": blr_apt,
                    "dep_offset_h": 12,
                    "duration_m": 100,
                    "base_fare": 3650.0,
                    "status": "Scheduled",
                    "terminal": "T1",
                    "gate": "G7",
                    "belt": "B2"
                },
                # Flight 7: CCU -> DEL
                {
                    "flight_number": "SG-263",
                    "airline": airline_map['SG'],
                    "aircraft": aircraft_map['VT-SGZ'],
                    "origin": ccu_apt,
                    "dest": del_apt,
                    "dep_offset_h": 14,
                    "duration_m": 140,
                    "base_fare": 4700.0,
                    "status": "Scheduled",
                    "terminal": "T1",
                    "gate": "G5",
                    "belt": "B3"
                },
                # Flight 8: MAA -> BOM
                {
                    "flight_number": "6E-417",
                    "airline": airline_map['6E'],
                    "aircraft": aircraft_map['VT-IFJ'],
                    "origin": maa_apt,
                    "dest": bom_apt,
                    "dep_offset_h": 16,
                    "duration_m": 115,
                    "base_fare": 3950.0,
                    "status": "Delayed",
                    "terminal": "T1",
                    "gate": "G3",
                    "belt": "B4"
                },
                # Flight 9: DEL -> GOI
                {
                    "flight_number": "AI-860",
                    "airline": airline_map['AI'],
                    "aircraft": aircraft_map['VT-EXA'],
                    "origin": del_apt,
                    "dest": goi_apt,
                    "dep_offset_h": 18,
                    "duration_m": 150,
                    "base_fare": 5800.0,
                    "status": "Scheduled",
                    "terminal": "T3",
                    "gate": "G15",
                    "belt": "B6"
                },
                # Flight 10: BLR -> COK
                {
                    "flight_number": "6E-392",
                    "airline": airline_map['6E'],
                    "aircraft": aircraft_map['VT-IFJ'],
                    "origin": blr_apt,
                    "dest": cok_apt,
                    "dep_offset_h": 20,
                    "duration_m": 65,
                    "base_fare": 2800.0,
                    "status": "Scheduled",
                    "terminal": "T1",
                    "gate": "G6",
                    "belt": "B1"
                },
                # Flight 11: DEL -> SXR
                {
                    "flight_number": "SG-104",
                    "airline": airline_map['SG'],
                    "aircraft": aircraft_map['VT-SGZ'],
                    "origin": del_apt,
                    "dest": sxr_apt,
                    "dep_offset_h": 22,
                    "duration_m": 85,
                    "base_fare": 4600.0,
                    "status": "Scheduled",
                    "terminal": "T1",
                    "gate": "G9",
                    "belt": "B2"
                },
                # Flight 12: BOM -> JAI
                {
                    "flight_number": "AI-611",
                    "airline": airline_map['AI'],
                    "aircraft": aircraft_map['VT-EXA'],
                    "origin": bom_apt,
                    "dest": jai_apt,
                    "dep_offset_h": 24,
                    "duration_m": 105,
                    "base_fare": 3800.0,
                    "status": "Scheduled",
                    "terminal": "T2",
                    "gate": "G11",
                    "belt": "B3"
                },
                # Flight 13: HYD -> VTZ
                {
                    "flight_number": "6E-728",
                    "airline": airline_map['6E'],
                    "aircraft": aircraft_map['VT-IFJ'],
                    "origin": hyd_apt,
                    "dest": vtz_apt,
                    "dep_offset_h": 26,
                    "duration_m": 70,
                    "base_fare": 3100.0,
                    "status": "Scheduled",
                    "terminal": "Main",
                    "gate": "G1",
                    "belt": "B1"
                },
                # Flight 14: GAU -> DEL
                {
                    "flight_number": "UK-742",
                    "airline": airline_map['UK'],
                    "aircraft": aircraft_map['VT-EXA'],
                    "origin": gau_apt,
                    "dest": del_apt,
                    "dep_offset_h": 28,
                    "duration_m": 155,
                    "base_fare": 5600.0,
                    "status": "Scheduled",
                    "terminal": "T1",
                    "gate": "G4",
                    "belt": "B2"
                },
                # Flight 15: DEL -> IXC
                {
                    "flight_number": "9I-831",
                    "airline": airline_map['9I'],
                    "aircraft": aircraft_map['VT-AAK'],
                    "origin": del_apt,
                    "dest": ixc_apt,
                    "dep_offset_h": 30,
                    "duration_m": 55,
                    "base_fare": 2400.0,
                    "status": "Scheduled",
                    "terminal": "T1",
                    "gate": "G2",
                    "belt": "B1"
                }
            ]

            created_flights = []
            for f_spec in sample_flights_def:
                if not f_spec['origin'] or not f_spec['dest']:
                    continue
                dep_dt = now + timedelta(hours=f_spec['dep_offset_h'])
                arr_dt = dep_dt + timedelta(minutes=f_spec['duration_m'])

                flight = Flight(
                    flight_number=f_spec['flight_number'],
                    airline_id=f_spec['airline'].id,
                    aircraft_id=f_spec['aircraft'].id,
                    origin_airport_id=f_spec['origin'].id,
                    destination_airport_id=f_spec['dest'].id,
                    scheduled_departure=dep_dt,
                    scheduled_arrival=arr_dt,
                    base_fare=f_spec['base_fare'],
                    status=f_spec['status'],
                    terminal=f_spec['terminal'],
                    gate=f_spec['gate'],
                    baggage_belt=f_spec['belt'],
                    data_source="Reference Schedule"
                )
                db.session.add(flight)
                db.session.flush()

                # Add initial status history
                history = FlightStatusHistory(
                    flight_id=flight.id,
                    previous_status=None,
                    new_status=flight.status,
                    source="Operational Schedule",
                    notes=f"Initial flight schedule recorded."
                )
                db.session.add(history)
                created_flights.append(flight)

            db.session.commit()
            print(f"Seeded {len(created_flights)} scheduled flights.")

            # 6. Seed Sample Bookings with Male & Female Passenger Seats!
            # This directly shows the blue & pink seat colors on the seat map.
            first_flight = Flight.query.filter_by(flight_number="AI-101").first()
            if first_flight and demo_passenger:
                # Find seats 4A (Male) and 4B (Female)
                seat_4a = AircraftSeat.query.filter_by(aircraft_id=first_flight.aircraft_id, row_number=4, seat_letter='A').first()
                seat_4b = AircraftSeat.query.filter_by(aircraft_id=first_flight.aircraft_id, row_number=4, seat_letter='B').first()
                seat_4c = AircraftSeat.query.filter_by(aircraft_id=first_flight.aircraft_id, row_number=4, seat_letter='C').first()

                if seat_4a and seat_4b and seat_4c:
                    booking = Booking(
                        booking_reference="IN-849201",
                        user_id=demo_passenger.id,
                        flight_id=first_flight.id,
                        booking_status="Confirmed",
                        passenger_count=3,
                        base_fare_total=first_flight.base_fare * 3,
                        seat_charge_total=seat_4a.additional_charge + seat_4b.additional_charge + seat_4c.additional_charge,
                        taxes_and_fees=round((first_flight.base_fare * 3) * 0.05 + 750.0, 2),
                        total_amount=round(first_flight.base_fare * 3 + seat_4a.additional_charge + seat_4b.additional_charge + seat_4c.additional_charge + ((first_flight.base_fare * 3) * 0.05 + 750.0), 2),
                        payment_mode="Demonstration Payment",
                        payment_status="Completed"
                    )
                    db.session.add(booking)
                    db.session.flush()

                    # Passenger 1: Male -> 4A (Will render in Male Blue #DCEBFF / #4385E8)
                    pax_male = Passenger(
                        booking_id=booking.id,
                        full_name="Rahul Verma",
                        gender_selection="Male",
                        age=32,
                        seat_number=seat_4a.seat_code,
                        cabin_class="Economy"
                    )
                    db.session.add(pax_male)
                    db.session.flush()

                    res_male = SeatReservation(
                        flight_id=first_flight.id,
                        aircraft_seat_id=seat_4a.id,
                        passenger_id=pax_male.id,
                        booking_id=booking.id,
                        reservation_status="Confirmed"
                    )
                    db.session.add(res_male)

                    # Passenger 2: Female -> 4B (Will render in Female Pink #FFE0EC / #E66B9A)
                    pax_female = Passenger(
                        booking_id=booking.id,
                        full_name="Ananya Verma",
                        gender_selection="Female",
                        age=29,
                        seat_number=seat_4b.seat_code,
                        cabin_class="Economy"
                    )
                    db.session.add(pax_female)
                    db.session.flush()

                    res_female = SeatReservation(
                        flight_id=first_flight.id,
                        aircraft_seat_id=seat_4b.id,
                        passenger_id=pax_female.id,
                        booking_id=booking.id,
                        reservation_status="Confirmed"
                    )
                    db.session.add(res_female)

                    # Passenger 3: Prefer not to say -> 4C (Will render in neutral gray)
                    pax_other = Passenger(
                        booking_id=booking.id,
                        full_name="Sam Verma",
                        gender_selection="Prefer not to say",
                        age=8,
                        seat_number=seat_4c.seat_code,
                        cabin_class="Economy"
                    )
                    db.session.add(pax_other)
                    db.session.flush()

                    res_other = SeatReservation(
                        flight_id=first_flight.id,
                        aircraft_seat_id=seat_4c.id,
                        passenger_id=pax_other.id,
                        booking_id=booking.id,
                        reservation_status="Confirmed"
                    )
                    db.session.add(res_other)

                    notif = Notification(
                        user_id=demo_passenger.id,
                        title="Welcome to Indian Airport Monitoring System",
                        message="Your sample booking IN-849201 for AI-101 has been confirmed. Explore the interactive map and seat selection!",
                        notification_type="booking"
                    )
                    db.session.add(notif)
                    db.session.commit()
                    print("Sample booking with Male (Blue) and Female (Pink) seats seeded successfully.")

        print("Database initialization and seeding completed successfully!")

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    seed_database(app)

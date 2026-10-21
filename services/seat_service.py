from datetime import datetime, timedelta
import random
import string
from extensions import db
from models.aircraft import Aircraft, AircraftSeat
from models.flight import Flight
from models.booking import Booking, SeatReservation, Passenger
from models.user import User

SAMPLE_MALE_NAMES = [
    "Rahul Verma", "Aarav Sharma", "Rohan Mehta", "Vikram Patel", "Rajesh Iyer",
    "Amit Gupta", "Suresh Kumar", "Aditya Singh", "Karthik Nair", "Deepak Joshi",
    "Manish Agarwal", "Nikhil Rao", "Sachin Bhatia", "Pranav Deshmukh", "Gaurav Malhotra",
    "Varun Kapoor", "Siddharth Jain", "Anand Kulkarni", "Mohit Bansal", "Harsh Vardhan"
]

SAMPLE_FEMALE_NAMES = [
    "Priya Sharma", "Ananya Verma", "Sneha Patel", "Pooja Mehta", "Deepika Iyer",
    "Sunita Gupta", "Kavita Singh", "Aishwarya Nair", "Neha Joshi", "Shreya Agarwal",
    "Divya Rao", "Ritu Bhatia", "Pallavi Deshmukh", "Komal Malhotra", "Tanvi Kapoor",
    "Rhea Jain", "Meenakshi Kulkarni", "Swati Bansal", "Aditi Rao", "Ishita Sen"
]

def ensure_flight_half_filled_seats(flight):
    """
    Guarantees that whenever seats for any flight are examined (especially Scheduled or Boarding),
    it is exactly half-filled (~48% - 52% of seat capacity),
    with Male seats in Blue (#DCEBFF / #4385E8),
    Female seats in Pink (#FFE0EC / #E66B9A),
    and the remaining half of the seats 100% available for booking.
    """
    if not flight or not flight.aircraft:
        return

    # Ensure seats exist
    if flight.aircraft.seats.count() == 0:
        generate_aircraft_seats(flight.aircraft_id)

    all_seats = AircraftSeat.query.filter_by(
        aircraft_id=flight.aircraft_id,
        is_active=True,
        restriction_status='Available'
    ).order_by(AircraftSeat.row_number.asc(), AircraftSeat.seat_letter.asc()).all()

    if not all_seats:
        return

    total_seats = len(all_seats)
    target_booked = total_seats // 2  # Exactly half filled

    confirmed_res = SeatReservation.query.filter_by(
        flight_id=flight.id,
        reservation_status='Confirmed'
    ).all()

    # If already around half filled or more, keep existing reservations
    if len(confirmed_res) >= target_booked - 3:
        return

    reserved_seat_ids = {r.aircraft_seat_id for r in confirmed_res}
    needed_count = target_booked - len(confirmed_res)
    unreserved_seats = [s for s in all_seats if s.id not in reserved_seat_ids]

    # Pick alternating unreserved seats to bring flight up to half filled
    seats_to_book = []
    for seat in unreserved_seats:
        if (seat.row_number + ord(seat.seat_letter)) % 2 == 0:
            seats_to_book.append(seat)
        if len(seats_to_book) >= needed_count:
            break

    if len(seats_to_book) < needed_count:
        for seat in unreserved_seats:
            if seat not in seats_to_book:
                seats_to_book.append(seat)
            if len(seats_to_book) >= needed_count:
                break

    # Get demo user
    demo_user = User.query.filter_by(role='passenger').first() or User.query.first()
    user_id = demo_user.id if demo_user else 1

    seat_idx = 0
    while seat_idx < len(seats_to_book):
        group_size = random.choices([1, 2, 3], weights=[50, 40, 10])[0]
        group = seats_to_book[seat_idx : seat_idx + group_size]
        seat_idx += len(group)
        if not group:
            break

        ref = "IN-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        pax_count = len(group)
        base_tot = flight.base_fare * pax_count
        seat_chg = sum(s.additional_charge for s in group)
        taxes = round(base_tot * 0.05 + 250.0 * pax_count, 2)
        total_amt = round(base_tot + seat_chg + taxes, 2)

        booking = Booking(
            booking_reference=ref,
            user_id=user_id,
            flight_id=flight.id,
            booking_status='Confirmed',
            passenger_count=pax_count,
            base_fare_total=base_tot,
            seat_charge_total=seat_chg,
            taxes_and_fees=taxes,
            total_amount=total_amt,
            payment_mode="Demonstration Payment",
            payment_status="Completed",
            created_at=flight.scheduled_departure - timedelta(days=1)
        )
        db.session.add(booking)
        db.session.flush()

        for s in group:
            roll = random.random()
            if roll < 0.48:
                gender = "Male"
                name = random.choice(SAMPLE_MALE_NAMES)
            elif roll < 0.96:
                gender = "Female"
                name = random.choice(SAMPLE_FEMALE_NAMES)
            else:
                gender = "Prefer not to say"
                name = random.choice(SAMPLE_MALE_NAMES)

            pax = Passenger(
                booking_id=booking.id,
                full_name=name,
                gender_selection=gender,
                age=random.randint(20, 65),
                seat_number=s.seat_code,
                cabin_class=s.cabin_class
            )
            db.session.add(pax)
            db.session.flush()

            res = SeatReservation(
                flight_id=flight.id,
                aircraft_seat_id=s.id,
                passenger_id=pax.id,
                booking_id=booking.id,
                reservation_status='Confirmed',
                created_at=booking.created_at
            )
            db.session.add(res)

    db.session.commit()

def generate_aircraft_seats(aircraft_id):
    """Populates standard seat records for an aircraft if none exist."""
    aircraft = Aircraft.query.get(aircraft_id)
    if not aircraft:
        return 0

    if aircraft.seats.count() > 0:
        return aircraft.seats.count()

    is_3_3 = (aircraft.layout_configuration == '3-3')
    letters = ['A', 'B', 'C', 'D', 'E', 'F'] if is_3_3 else ['A', 'C', 'D', 'F']
    total_rows = aircraft.total_rows or 30

    created = 0
    for row in range(1, total_rows + 1):
        # Determine cabin class and seat types
        if row <= 2:
            cabin = 'Business'
            extra_charge = 1500.0
        elif row <= 5:
            cabin = 'Premium Economy'
            extra_charge = 500.0
        else:
            cabin = 'Economy'
            extra_charge = 0.0

        is_exit_row = (row in [12, 13])

        for letter in letters:
            # Determine seat type
            if is_exit_row:
                seat_type = 'Emergency Exit'
                charge = 750.0
            elif letter in ['A', 'F']:
                seat_type = 'Window'
                charge = extra_charge if cabin != 'Economy' else 250.0
            elif letter in ['C', 'D']:
                seat_type = 'Aisle'
                charge = extra_charge if cabin != 'Economy' else 200.0
            else:
                seat_type = 'Middle'
                charge = extra_charge if cabin != 'Economy' else 0.0

            # Restricted seats (e.g. crew last row)
            restricted = (row == total_rows and letter in ['E', 'F'])
            status = 'Restricted' if restricted else 'Available'

            seat = AircraftSeat(
                aircraft_id=aircraft.id,
                row_number=row,
                seat_letter=letter,
                cabin_class=cabin,
                seat_type=seat_type,
                additional_charge=charge,
                restriction_status=status,
                is_active=True
            )
            db.session.add(seat)
            created += 1

    db.session.commit()
    return created

def get_flight_seat_map(flight_id, current_user_id=None):
    """
    Returns cabin layout matrix with dynamic visual states:
    - 'available'
    - 'occupied_male' (Male passenger booked -> #DCEBFF / #4385E8)
    - 'occupied_female' (Female passenger booked -> #FFE0EC / #E66B9A)
    - 'occupied_other' (Gender undisclosed -> Neutral gray)
    - 'restricted'
    - 'held'
    """
    flight = Flight.query.get(flight_id)
    if not flight:
        return None

    # Ensure seats exist
    if flight.aircraft.seats.count() == 0:
        generate_aircraft_seats(flight.aircraft_id)

    # Ensure half-filled seats when examined
    ensure_flight_half_filled_seats(flight)

    # Fetch all seats ordered by row and letter
    seats = AircraftSeat.query.filter_by(aircraft_id=flight.aircraft_id, is_active=True)\
        .order_by(AircraftSeat.row_number.asc(), AircraftSeat.seat_letter.asc()).all()

    # Fetch active reservations for this flight
    active_reservations = SeatReservation.query.filter(
        SeatReservation.flight_id == flight.id,
        SeatReservation.reservation_status.in_(['Confirmed', 'Held'])
    ).all()

    reservation_map = {}
    for res in active_reservations:
        reservation_map[res.aircraft_seat_id] = res

    # Build rows mapping
    rows_dict = {}
    is_3_3 = (flight.aircraft.layout_configuration == '3-3')
    seat_letters = ['A', 'B', 'C', 'D', 'E', 'F'] if is_3_3 else ['A', 'C', 'D', 'F']

    for seat in seats:
        row = seat.row_number
        if row not in rows_dict:
            rows_dict[row] = {
                'row_number': row,
                'cabin_class': seat.cabin_class,
                'is_exit_row': (seat.seat_type == 'Emergency Exit'),
                'seats': []
            }

        # Determine visual state
        res = reservation_map.get(seat.id)
        if seat.restriction_status != 'Available':
            state = 'restricted'
            gender_color = 'restricted'
        elif res:
            if res.reservation_status == 'Held':
                state = 'held'
                gender_color = 'held'
            else:
                state = 'occupied'
                # Check passenger gender
                if res.passenger:
                    if res.passenger.gender_selection == 'Male':
                        gender_color = 'male'  # Blue #DCEBFF
                    elif res.passenger.gender_selection == 'Female':
                        gender_color = 'female'  # Pink #FFE0EC
                    else:
                        gender_color = 'other'  # Neutral gray
                else:
                    gender_color = 'other'
        else:
            state = 'available'
            gender_color = 'available'

        seat_data = {
            'id': seat.id,
            'seat_code': seat.seat_code,
            'row': seat.row_number,
            'letter': seat.seat_letter,
            'cabin_class': seat.cabin_class,
            'seat_type': seat.seat_type,
            'charge': seat.additional_charge,
            'state': state,
            'gender_color': gender_color,
            'is_available': (state == 'available')
        }
        rows_dict[row]['seats'].append(seat_data)

    sorted_rows = [rows_dict[r] for r in sorted(rows_dict.keys())]

    return {
        'flight_id': flight.id,
        'flight_number': flight.flight_number,
        'aircraft_model': flight.aircraft.model,
        'aircraft_registration': flight.aircraft.registration,
        'layout_type': flight.aircraft.layout_configuration,
        'seat_letters': seat_letters,
        'rows': sorted_rows,
        'total_seats': len(seats),
        'available_seats': sum(1 for s in seats if s.id not in reservation_map and s.restriction_status == 'Available')
    }

def validate_seats_available(flight_id, seat_ids):
    """
    Validates that each requested seat ID is available and not reserved for this flight.
    Returns (is_valid, list_of_conflicts_or_seats)
    """
    if not seat_ids:
        return False, "No seats selected."

    # Fetch seats
    seats = AircraftSeat.query.filter(AircraftSeat.id.in_(seat_ids)).all()
    if len(seats) != len(seat_ids):
        return False, "One or more invalid seat identifiers."

    # Check for active reservations
    conflicts = SeatReservation.query.filter(
        SeatReservation.flight_id == flight_id,
        SeatReservation.aircraft_seat_id.in_(seat_ids),
        SeatReservation.reservation_status.in_(['Confirmed', 'Held'])
    ).all()

    if conflicts:
        conflict_seat_ids = [c.aircraft_seat_id for c in conflicts]
        conflicted_codes = [s.seat_code for s in seats if s.id in conflict_seat_ids]
        return False, f"Seats already booked or held: {', '.join(conflicted_codes)}"

    # Check restrictions
    for s in seats:
        if s.restriction_status != 'Available':
            return False, f"Seat {s.seat_code} is restricted and cannot be booked."

    return True, seats

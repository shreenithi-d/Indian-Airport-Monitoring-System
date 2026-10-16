from utils.security import generate_booking_reference
from models import Booking


def unique_booking_reference():
    """Generate a booking reference guaranteed to be unique in the DB."""
    for _ in range(10):
        ref = generate_booking_reference()
        existing = Booking.query.filter_by(internal_booking_reference=ref).first()
        if not existing:
            return ref
    raise RuntimeError('Could not generate unique booking reference after 10 attempts.')

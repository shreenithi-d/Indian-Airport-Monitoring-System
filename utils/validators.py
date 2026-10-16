import re

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

def validate_email_format(email):
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))

def validate_password_strength(password):
    """
    Checks that password has minimum length of 6 characters.
    """
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""

def validate_coordinates(lat, lon):
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        if not (-90.0 <= lat_f <= 90.0):
            return False, "Latitude must be between -90 and 90."
        if not (-180.0 <= lon_f <= 180.0):
            return False, "Longitude must be between -180 and 180."
        return True, ""
    except (ValueError, TypeError):
        return False, "Coordinates must be valid decimal numbers."

def validate_iata_code(code):
    if not code:
        return True, ""
    code = code.strip().upper()
    if len(code) != 3 or not code.isalpha():
        return False, "IATA code must be exactly 3 uppercase letters."
    return True, ""

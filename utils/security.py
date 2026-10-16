import secrets
import string
from flask import request
from extensions import db
from datetime import datetime, timezone


def generate_booking_reference():
    """Generate a unique 10-char booking reference: 2 letters + 8 digits."""
    prefix = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))
    digits = ''.join(secrets.choice(string.digits) for _ in range(8))
    return f'{prefix}{digits}'


def generate_idempotency_key():
    return secrets.token_hex(32)


def log_audit(user_id, action, resource_type=None, resource_id=None, details=None):
    from models import AuditLog
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr if request else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()


def mask_passport(number):
    if not number:
        return ''
    if len(number) <= 4:
        return '****'
    return '*' * (len(number) - 4) + number[-4:]

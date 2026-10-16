from urllib.parse import urlparse, urljoin
from flask import request

def is_safe_url(target):
    """Prevents open redirect attacks by ensuring target redirect is on same host."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def format_currency(amount):
    """Formats number in Indian numbering format (e.g., ₹4,500.00)."""
    try:
        return f"₹{float(amount):,.2f}"
    except (ValueError, TypeError):
        return f"₹{amount}"

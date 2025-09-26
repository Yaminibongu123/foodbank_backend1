import re
from datetime import datetime

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

def format_date(date_string):
    try:
        if isinstance(date_string, str):
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return date_string
    except:
        return None

def calculate_impact_score(donations_count, requests_count):
    return donations_count * 10 + requests_count * 5
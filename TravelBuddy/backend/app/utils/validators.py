"""Validation utilities"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_chat_request(data: Dict) -> Dict:
    """Validate chat request data"""
    
    errors = []
    
    if 'message' not in data or not data['message']:
        errors.append("Message is required")
    elif len(data['message']) > 5000:
        errors.append("Message is too long (max 5000 characters)")
    
    if 'user_id' not in data or not data['user_id']:
        errors.append("User ID is required")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_hotel_search(data: Dict) -> Dict:
    """Validate hotel search parameters"""
    
    errors = []
    
    if 'query' not in data or not data['query']:
        errors.append("Search query is required")
    
    if 'max_price' in data:
        price = data['max_price']
        if not isinstance(price, (int, float)) or price < 0:
            errors.append("Invalid max_price")
        elif price > 1000000:
            errors.append("max_price is too high")
    
    if 'min_rating' in data:
        rating = data['min_rating']
        if not isinstance(rating, (int, float)) or rating < 0 or rating > 5:
            errors.append("min_rating must be between 0 and 5")
    
    if 'limit' in data:
        limit = data['limit']
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            errors.append("limit must be between 1 and 50")
            
    if 'required_amenities' in data:
        if not isinstance(data['required_amenities'], list):
            errors.append("required_amenities must be a list")
        else:
            valid_amenities = {
                'pool', 'spa', 'wifi', 'restaurant', 'gym', 'parking',
                'beach_access', 'room_service', 'bar', 'conference_room',
                'children_activities', 'airport_shuttle'
            }
            for amenity in data['required_amenities']:
                if amenity not in valid_amenities:
                    errors.append(f"Invalid amenity: {amenity}")
    
    if 'travel_group' in data:
        valid_groups = {'solo', 'couple', 'family', 'friends', 'business'}
        if data['travel_group'] not in valid_groups:
            errors.append("Invalid travel_group type")
    
    if 'season' in data:
        valid_seasons = {
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        }
        if data['season'].lower() not in valid_seasons:
            errors.append("Invalid season")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_booking_request(data: Dict) -> Dict:
    """Validate booking request"""
    
    errors = []
    
    required = ['user_id', 'item_type', 'item_id', 'details']
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if 'item_type' in data:
        if data['item_type'] not in ['hotel', 'attraction']:
            errors.append("item_type must be 'hotel' or 'attraction'")
    
    if 'details' in data:
        details_validation = validate_booking_details(
            data.get('item_type'),
            data['details']
        )
        if not details_validation['valid']:
            errors.extend(details_validation['errors'])
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_booking_details(item_type: str, details: Dict) -> Dict:
    """Validate booking details based on item type"""
    
    errors = []
    
    if item_type == 'hotel':
        required = ['check_in', 'check_out', 'guests', 'rooms']
        for field in required:
            if field not in details:
                errors.append(f"Missing required field: {field}")
        
        # Validate dates
        if 'check_in' in details and 'check_out' in details:
            date_validation = validate_date_range(
                details['check_in'],
                details['check_out']
            )
            if not date_validation['valid']:
                errors.extend(date_validation['errors'])
        
        # Validate guests and rooms
        if 'guests' in details:
            if not isinstance(details['guests'], int) or details['guests'] < 1:
                errors.append("guests must be a positive integer")
        
        if 'rooms' in details:
            if not isinstance(details['rooms'], int) or details['rooms'] < 1:
                errors.append("rooms must be a positive integer")
    
    elif item_type == 'attraction':
        required = ['visit_date', 'visitors']
        for field in required:
            if field not in details:
                errors.append(f"Missing required field: {field}")
        
        # Validate visit date
        if 'visit_date' in details:
            date_validation = validate_future_date(details['visit_date'])
            if not date_validation['valid']:
                errors.extend(date_validation['errors'])
        
        # Validate visitors
        if 'visitors' in details:
            if not isinstance(details['visitors'], int) or details['visitors'] < 1:
                errors.append("visitors must be a positive integer")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_date_range(start_date: str, end_date: str) -> Dict:
    """Validate date range"""
    
    errors = []
    
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        now = datetime.now()
        
        # Check if start is in the past
        if start.date() < now.date():
            errors.append("Start date cannot be in the past")
        
        # Check if end is before start
        if end <= start:
            errors.append("End date must be after start date")
        
        # Check if range is too long (e.g., more than 1 year)
        if (end - start).days > 365:
            errors.append("Date range cannot exceed 365 days")
        
    except ValueError as e:
        errors.append(f"Invalid date format: {str(e)}")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_future_date(date_str: str, min_days_ahead: int = 0) -> Dict:
    """Validate that date is in the future"""
    
    errors = []
    
    try:
        date = datetime.fromisoformat(date_str)
        now = datetime.now()
        
        min_date = now + timedelta(days=min_days_ahead)
        
        if date.date() < min_date.date():
            if min_days_ahead > 0:
                errors.append(f"Date must be at least {min_days_ahead} days in the future")
            else:
                errors.append("Date cannot be in the past")
        
    except ValueError as e:
        errors.append(f"Invalid date format: {str(e)}")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_itinerary_request(data: Dict) -> Dict:
    """Validate itinerary generation request"""
    
    errors = []
    
    if 'duration_days' not in data:
        errors.append("duration_days is required")
    elif not isinstance(data['duration_days'], int):
        errors.append("duration_days must be an integer")
    elif data['duration_days'] < 1 or data['duration_days'] > 30:
        errors.append("duration_days must be between 1 and 30")
    
    if 'interests' not in data:
        errors.append("interests are required")
    elif not isinstance(data['interests'], list):
        errors.append("interests must be a list")
    elif len(data['interests']) == 0:
        errors.append("At least one interest is required")
    
    if 'budget' not in data:
        errors.append("budget is required")
    elif not isinstance(data['budget'], (int, float)):
        errors.append("budget must be a number")
    elif data['budget'] < 1000:
        errors.append("budget seems too low")
    elif data['budget'] > 10000000:
        errors.append("budget seems too high")
    
    if 'start_date' in data:
        date_validation = validate_future_date(data['start_date'])
        if not date_validation['valid']:
            errors.extend(date_validation['errors'])
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_user_id(user_id: str) -> Dict:
    """Validate user ID format"""
    
    errors = []
    
    if not user_id or not isinstance(user_id, str):
        errors.append("user_id must be a non-empty string")
    elif len(user_id) > 100:
        errors.append("user_id is too long")
    elif not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
        errors.append("user_id contains invalid characters")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_email(email: str) -> Dict:
    """Validate email format"""
    
    errors = []
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email:
        errors.append("email is required")
    elif not re.match(pattern, email):
        errors.append("Invalid email format")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def validate_phone(phone: str) -> Dict:
    """Validate phone number"""
    
    errors = []
    
    # Remove spaces and special characters
    cleaned = re.sub(r'[^\d]', '', phone)
    
    if not cleaned:
        errors.append("phone is required")
    elif len(cleaned) != 10:
        errors.append("Phone number must be 10 digits")
    elif not cleaned.isdigit():
        errors.append("Phone number must contain only digits")
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

def sanitize_input(text: str, max_length: int = 5000) -> str:
    """Sanitize user input"""
    
    if not isinstance(text, str):
        return ""
    
    # Remove any potentially harmful characters
    text = re.sub(r'[<>]', '', text)
    
    # Limit length
    text = text[:max_length]
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def validate_price_comparison_request(data: Dict) -> Dict:
    """Validate price comparison request"""
    
    errors = []
    
    required = ['location', 'check_in', 'check_out']
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if 'check_in' in data and 'check_out' in data:
        date_validation = validate_date_range(
            data['check_in'],
            data['check_out']
        )
        if not date_validation['valid']:
            errors.extend(date_validation['errors'])
    
    if errors:
        return {'valid': False, 'errors': errors}
    
    return {'valid': True, 'errors': []}

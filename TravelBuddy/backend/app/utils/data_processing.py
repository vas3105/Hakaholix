"""Data processing utilities"""

import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(_name_)

def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string to number of days"""
    
    duration_str = duration_str.lower().strip()
    
    # Match patterns like "5 days", "1 week", "2 nights"
    patterns = [
        (r'(\d+)\s*days?', 1),
        (r'(\d+)\s*nights?', 1),
        (r'(\d+)\s*weeks?', 7),
        (r'(\d+)\s*months?', 30)
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, duration_str)
        if match:
            return int(match.group(1)) * multiplier
    
    return None

def parse_budget(budget_str: str) -> Optional[int]:
    """Parse budget string to number"""
    
    budget_str = str(budget_str).lower().strip()
    
    # Skip if it looks like a duration pattern
    if re.search(r'\d+\s*(day|night|week|month)', budget_str):
        return None
    
    # Remove common prefixes
    budget_str = re.sub(r'(rs\.?|inr|₹)\s*', '', budget_str)
    
    # Handle K/L notation
    budget_str = budget_str.replace(',', '')
    
    if 'k' in budget_str:
        num = re.search(r'([\d.]+)k', budget_str)
        if num:
            return int(float(num.group(1)) * 1000)
    
    if 'l' in budget_str or 'lakh' in budget_str:
        num = re.search(r'([\d.]+)l', budget_str)
        if num:
            return int(float(num.group(1)) * 100000)
    
    # Look for "budget" keyword followed by number
    budget_match = re.search(r'budget[:\s]+(\d+)', budget_str)
    if budget_match:
        return int(budget_match.group(1))
    
    # Look for price/cost keywords
    price_match = re.search(r'(price|cost|spend)[:\s]+(\d+)', budget_str)
    if price_match:
        return int(price_match.group(2))
    
    # Only extract direct large numbers (avoid confusion with days)
    num = re.search(r'(\d{4,})', budget_str)  # At least 4 digits
    if num:
        return int(num.group(1))
    
    return None

def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to ISO format"""
    
    date_formats = [
        '%Y-%m-%d',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%B %d, %Y',
        '%d %B %Y',
        '%b %d, %Y',
        '%d %b %Y'
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None

def extract_locations(text: str, known_locations: List[str] = None) -> List[str]:
    """Extract location mentions from text"""
    
    if known_locations is None:
        known_locations = [
            'kochi', 'cochin', 'trivandrum', 'thiruvananthapuram',
            'munnar', 'alleppey', 'alappuzha', 'kovalam', 'wayanad',
            'thekkady', 'periyar', 'varkala', 'kumarakom', 'fort kochi',
            'mattancherry', 'ernakulam', 'thrissur', 'kannur', 'kasaragod',
            'kollam', 'kottayam', 'idukki', 'palakkad', 'kozhikode', 'calicut'
        ]
    
    text_lower = text.lower()
    found_locations = []
    
    for location in known_locations:
        if location in text_lower:
            # Capitalize properly
            found_locations.append(location.title())
    
    return list(set(found_locations))

def extract_interests(text: str) -> List[str]:
    """Extract travel interests from text"""
    
    interest_keywords = {
        'beach': ['beach', 'sea', 'coast', 'shore', 'surf'],
        'nature': ['nature', 'forest', 'wildlife', 'jungle', 'trekking', 'hiking'],
        'culture': ['culture', 'temple', 'church', 'heritage', 'history', 'traditional'],
        'adventure': ['adventure', 'sports', 'rafting', 'climbing', 'zip line'],
        'relaxation': ['relax', 'spa', 'ayurveda', 'massage', 'peaceful', 'calm'],
        'food': ['food', 'cuisine', 'restaurant', 'dining', 'culinary'],
        'backwaters': ['backwater', 'houseboat', 'canal', 'lagoon'],
        'hill station': ['hill', 'mountain', 'tea garden', 'plantation'],
        'shopping': ['shopping', 'market', 'bazaar', 'handicraft']
    }
    
    text_lower = text.lower()
    interests = []
    
    for interest, keywords in interest_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            interests.append(interest)
    
    return interests

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters except basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    
    return text.strip()

def chunk_text(text: str, max_chunk_size: int = 500) -> List[str]:
    """Split text into chunks"""
    
    sentences = re.split(r'[.!?]+', text)
    chunks = []
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_size = len(sentence)
        
        if current_size + sentence_size > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_size
        else:
            current_chunk.append(sentence)
            current_size += sentence_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def format_price(amount: float, currency: str = 'INR') -> str:
    """Format price for display"""
    
    if currency == 'INR':
        # Indian number formatting
        s = str(int(amount))
        if len(s) <= 3:
            return f'₹{s}'
        
        # Add commas
        result = s[-3:]
        s = s[:-3]
        while s:
            result = s[-2:] + ',' + result
            s = s[:-2]
        
        return f'₹{result}'
    
    return f'{currency} {amount:,.2f}'

def calculate_date_range(start_date: str, duration_days: int) -> Dict[str, str]:
    """Calculate date range from start date and duration"""
    
    start = datetime.fromisoformat(start_date)
    end = start + timedelta(days=duration_days)
    
    return {
        'start_date': start.strftime('%Y-%m-%d'),
        'end_date': end.strftime('%Y-%m-%d'),
        'start_day': start.strftime('%A'),
        'end_day': end.strftime('%A'),
        'duration_days': duration_days
    }

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate Indian phone number"""
    # Remove spaces and special characters
    phone = re.sub(r'[^\d]', '', phone)
    
    # Should be 10 digits
    return len(phone) == 10 and phone.isdigit()

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    
    return filename

def merge_dicts_deep(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts_deep(result[key], value)
        else:
            result[key] = value
    
    return result

def extract_numbers(text: str) -> List[int]:
    """Extract all numbers from text"""
    return [int(n) for n in re.findall(r'\d+', text)]

def fuzzy_match_location(query: str, locations: List[str], threshold: float = 0.7) -> List[str]:
    """Find locations with fuzzy matching"""
    
    from difflib import SequenceMatcher
    
    matches = []
    query_lower = query.lower()
    
    for location in locations:
        location_lower = location.lower()
        
        # Check exact substring match
        if query_lower in location_lower or location_lower in query_lower:
            matches.append((location, 1.0))
            continue
        
        # Calculate similarity
        similarity = SequenceMatcher(None, query_lower, location_lower).ratio()
        
        if similarity >= threshold:
            matches.append((location, similarity))
    
    # Sort by similarity
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return [location for location, _ in matches]

def parse_number_of_people(text: str) -> Optional[int]:
    """Extract number of people from text"""
    
    patterns = [
        r'(\d+)\s*people',
        r'(\d+)\s*persons?',
        r'(\d+)\s*travelers?',
        r'(\d+)\s*guests?',
        r'(\d+)\s*adults?',
        r'group\s*of\s*(\d+)',
        r'party\s*of\s*(\d+)'
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))
    
    # Check for words like "couple", "family"
    if 'couple' in text_lower:
        return 2
    if 'solo' in text_lower or 'alone' in text_lower:
        return 1
    if 'family' in text_lower:
        return 4  # Average family size
    
    return None

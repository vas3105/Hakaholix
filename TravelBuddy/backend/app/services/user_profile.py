import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(_name_)

class UserProfileService:
    """Manages user profiles for personalization"""
    
    def _init_(self, storage_dir: str = "./data/user_profiles"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def get_profile(self, user_id: str) -> Dict:
        """Get user profile or create new one"""
        
        profile_path = self.storage_dir / f"{user_id}.json"
        
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                profile = json.load(f)
        else:
            # Create new profile with defaults
            profile = self._create_default_profile(user_id)
            self._save_profile(user_id, profile)
        
        return profile
    
    def update_profile(self, user_id: str, updates: Dict):
        """Update user profile"""
        
        profile = self.get_profile(user_id)
        
        # Update interests (append and deduplicate)
        if 'interests' in updates:
            existing = set(profile.get('interests', []))
            new_interests = set(updates['interests'])
            profile['interests'] = list(existing.union(new_interests))
        
        # Update budget category
        if 'budget_category' in updates:
            profile['budget_category'] = updates['budget_category']
        
        # Update travel style
        if 'travel_style' in updates:
            profile['travel_style'] = updates['travel_style']
        
        # Track search history
        if 'search_query' in updates:
            if 'search_history' not in profile:
                profile['search_history'] = []
            
            profile['search_history'].append({
                'query': updates['search_query'],
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 50 searches
            profile['search_history'] = profile['search_history'][-50:]
        
        # Update last interaction
        profile['last_interaction'] = datetime.now().isoformat()
        
        self._save_profile(user_id, profile)
    
    def add_booking(self, user_id: str, booking: Dict):
        """Add booking to user history"""
        
        profile = self.get_profile(user_id)
        
        if 'bookings' not in profile:
            profile['bookings'] = []
        
        booking['timestamp'] = datetime.now().isoformat()
        profile['bookings'].append(booking)
        
        self._save_profile(user_id, profile)
    
    def get_recommendations(self, user_id: str) -> Dict:
        """Generate personalized recommendations based on profile"""
        
        profile = self.get_profile(user_id)
        
        recommendations = {
            'preferred_budget_range': self._get_budget_range(profile),
            'suggested_interests': profile.get('interests', []),
            'travel_style': profile.get('travel_style', 'balanced'),
            'previous_destinations': self._get_previous_destinations(profile)
        }
        
        return recommendations
        
    def get_preferences(self, user_id: str) -> Dict:
        """Get all user preferences including embeddings and learned preferences"""
        from app.main import preferences_model
        
        # Return all preference data for the user
        return preferences_model
    
    def _create_default_profile(self, user_id: str) -> Dict:
        """Create default user profile"""
        
        return {
            'user_id': user_id,
            'interests': [],
            'budget_category': 'moderate',
            'travel_style': 'balanced',
            'search_history': [],
            'bookings': [],
            'preferences': {
                'accommodation_type': [],
                'activities': [],
                'cuisine': []
            },
            'created_at': datetime.now().isoformat(),
            'last_interaction': datetime.now().isoformat()
        }
    
    def _save_profile(self, user_id: str, profile: Dict):
        """Save profile to disk"""
        
        profile_path = self.storage_dir / f"{user_id}.json"
        
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)
    
    def _get_budget_range(self, profile: Dict) -> Dict:
        """Get budget range based on category"""
        
        category = profile.get('budget_category', 'moderate')
        
        ranges = {
            'budget': {'min': 0, 'max': 5000},
            'moderate': {'min': 5000, 'max': 15000},
            'luxury': {'min': 15000, 'max': 50000}
        }
        
        return ranges.get(category, ranges['moderate'])
    
    def _get_previous_destinations(self, profile: Dict) -> List[str]:
        """Extract previous destinations from bookings"""
        
        bookings = profile.get('bookings', [])
        destinations = []
        
        for booking in bookings:
            if 'destination' in booking:
                destinations.append(booking['destination'])
        
        return list(set(destinations))

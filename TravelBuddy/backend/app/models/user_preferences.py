"""User preferences and personalization model."""

from typing import Dict, List, Optional
from datetime import datetime
import numpy as np
from sentence_transformers import SentenceTransformer

class UserPreferences:
    """Handles user preference learning and recommendation personalization"""
    
    def _init_(self, embedding_model: str):
        self.embedder = SentenceTransformer(embedding_model)
        self.user_embeddings = {}
        self.preference_vectors = {}
        self.seasonal_preferences = {}
        self.travel_group_preferences = {}
        self.amenity_preferences = {}
    
    def update_preferences(
        self,
        user_id: str,
        interactions: List[Dict],
        profile: Dict
    ):
        """Update user preferences based on interactions and profile"""
        
        # Combine all interaction text
        texts = []
        
        # Add search queries
        texts.extend([i['query'] for i in interactions if 'query' in i])
        
        # Add clicked items
        texts.extend([i['item_name'] for i in interactions if 'item_name' in i])
        
        # Add profile interests
        if 'interests' in profile:
            texts.extend(profile['interests'])
            
        if 'travel_style' in profile:
            texts.append(profile['travel_style'])
            
        if 'preferred_activities' in profile:
            texts.extend(profile['preferred_activities'])
            
        # Update seasonal preferences
        if 'travel_season' in profile:
            self._update_seasonal_preferences(user_id, profile['travel_season'])
            
        # Update travel group preferences
        if 'travel_group' in profile:
            self._update_travel_group_preferences(
                user_id,
                profile['travel_group'],
                profile.get('special_requirements', [])
            )
            
        # Update amenity preferences
        if 'preferred_amenities' in profile:
            self._update_amenity_preferences(user_id, profile['preferred_amenities'])
        
        if texts:
            # Create embeddings
            embeddings = self.embedder.encode(texts)
            
            # Average the embeddings
            avg_embedding = np.mean(embeddings, axis=0)
            
            # Update user embedding
            self.user_embeddings[user_id] = avg_embedding
            
            # Update preference vectors
            self._update_preference_vectors(user_id, interactions)
    
    def _update_preference_vectors(
        self,
        user_id: str,
        interactions: List[Dict]
    ):
        """Update category-specific preference vectors"""
        
        categories = ['hotels', 'attractions', 'activities']
        
        for category in categories:
            relevant_items = [
                i for i in interactions 
                if i.get('category') == category and i.get('rating')
            ]
            
            if relevant_items:
                # Get item embeddings and ratings
                items = [i['item_name'] for i in relevant_items]
                ratings = [i['rating'] for i in relevant_items]
                
                embeddings = self.embedder.encode(items)
                ratings = np.array(ratings)
                
                # Weighted average based on ratings
                weights = (ratings - ratings.min()) / (ratings.max() - ratings.min() + 1e-6)
                weighted_avg = np.average(embeddings, weights=weights, axis=0)
                
                if user_id not in self.preference_vectors:
                    self.preference_vectors[user_id] = {}
                
                self.preference_vectors[user_id][category] = weighted_avg
    
    def _update_seasonal_preferences(self, user_id: str, season: str):
        """Update seasonal preferences for user"""
        if user_id not in self.seasonal_preferences:
            self.seasonal_preferences[user_id] = {}
        
        current_month = datetime.now().strftime('%B')
        
        # Weight recent seasons more heavily
        current_weight = 0.7 if season.lower() == current_month.lower() else 0.3
        
        if season in self.seasonal_preferences[user_id]:
            self.seasonal_preferences[user_id][season] += current_weight
        else:
            self.seasonal_preferences[user_id][season] = current_weight
    
    def _update_travel_group_preferences(
        self,
        user_id: str,
        group_type: str,
        special_requirements: List[str]
    ):
        """Update travel group preferences"""
        if user_id not in self.travel_group_preferences:
            self.travel_group_preferences[user_id] = {
                'types': {},
                'requirements': set()
            }
        
        # Update group type frequency
        if group_type in self.travel_group_preferences[user_id]['types']:
            self.travel_group_preferences[user_id]['types'][group_type] += 1
        else:
            self.travel_group_preferences[user_id]['types'][group_type] = 1
        
        # Update special requirements
        if special_requirements:
            self.travel_group_preferences[user_id]['requirements'].update(special_requirements)
    
    def _update_amenity_preferences(self, user_id: str, amenities: List[str]):
        """Update amenity preferences with weights"""
        if user_id not in self.amenity_preferences:
            self.amenity_preferences[user_id] = {}
        
        for amenity in amenities:
            if amenity in self.amenity_preferences[user_id]:
                self.amenity_preferences[user_id][amenity] += 1
            else:
                self.amenity_preferences[user_id][amenity] = 1
    
    def get_personalized_scores(
        self,
        user_id: str,
        items: List[Dict],
        category: str
    ) -> List[float]:
        """Get personalization scores for items"""
        
        if not items:
            return []
            
        # Get embeddings for items
        texts = [i['document'] for i in items]
        item_embeddings = self.embedder.encode(texts)
        
        # Get user preferences
        user_emb = self.user_embeddings.get(user_id)
        category_emb = self.preference_vectors.get(user_id, {}).get(category)
        
        if user_emb is None and category_emb is None:
            return [1.0] * len(items)  # No personalization
        
        scores = []
        current_month = datetime.now().strftime('%B').lower()
        
        for idx, (item_emb, item) in enumerate(zip(item_embeddings, items)):
            score = 1.0  # Base score
            
            # Factor in general user preferences (30% weight)
            if user_emb is not None:
                user_sim = np.dot(item_emb, user_emb) / (
                    np.linalg.norm(item_emb) * np.linalg.norm(user_emb)
                )
                score *= 0.3 * (1 + user_sim)
            
            # Factor in category-specific preferences (20% weight)
            if category_emb is not None:
                cat_sim = np.dot(item_emb, category_emb) / (
                    np.linalg.norm(item_emb) * np.linalg.norm(category_emb)
                )
                score *= 0.2 * (1 + cat_sim)
            
            # Factor in seasonal preferences (15% weight)
            if user_id in self.seasonal_preferences:
                season_score = 1.0
                seasons = item['metadata'].get('best_seasons', [current_month])
                for season in seasons:
                    if season.lower() in self.seasonal_preferences[user_id]:
                        season_score *= (1 + self.seasonal_preferences[user_id][season.lower()])
                score *= 0.15 * season_score
            
            # Factor in travel group preferences (20% weight)
            if user_id in self.travel_group_preferences:
                group_score = 1.0
                
                # Check if hotel amenities match group requirements
                requirements = self.travel_group_preferences[user_id]['requirements']
                amenities = set(item['metadata'].get('amenities', []))
                if requirements:
                    matches = len(requirements.intersection(amenities))
                    group_score *= (1 + matches / len(requirements))
                
                # Check if hotel type matches group type
                group_types = self.travel_group_preferences[user_id]['types']
                if group_types:
                    hotel_type = item['metadata'].get('type', '').lower()
                    if hotel_type in ['family', 'resort'] and 'family' in group_types:
                        group_score *= 1.5
                    elif hotel_type in ['boutique', 'villa'] and 'couple' in group_types:
                        group_score *= 1.5
                
                score *= 0.2 * group_score
            
            # Factor in amenity preferences (15% weight)
            if user_id in self.amenity_preferences:
                amenity_score = 1.0
                item_amenities = set(item['metadata'].get('amenities', []))
                
                for amenity, weight in self.amenity_preferences[user_id].items():
                    if amenity.lower() in [a.lower() for a in item_amenities]:
                        amenity_score *= (1 + (weight / 10))  # Normalize weight
                
                score *= 0.15 * amenity_score
            
            scores.append(float(score))
        
        # Normalize scores to 0-1 range
        if scores:
            min_score = min(scores)
            max_score = max(scores)
            if max_score > min_score:
                scores = [(s - min_score) / (max_score - min_score) for s in scores]
        
        return scores

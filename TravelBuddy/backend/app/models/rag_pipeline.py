import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(_name_)

class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for travel data"""
    
    def _init_(
        self,
        embedding_model: str,
        persist_directory: str
    ):
        # Initialize embedding model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client(
            ChromaSettings(
                persist_directory=persist_directory,
                anonymized_telemetry=False
            )
        )
        
        # Create collections
        self.hotels_collection = self.chroma_client.get_or_create_collection(
            name="hotels",
            metadata={"description": "Kerala hotels data"}
        )
        
        self.attractions_collection = self.chroma_client.get_or_create_collection(
            name="attractions",
            metadata={"description": "Kerala attractions data"}
        )
        
        self.itineraries_collection = self.chroma_client.get_or_create_collection(
            name="itineraries",
            metadata={"description": "Travel itinerary templates"}
        )
        
        logger.info("RAG pipeline initialized")
    
    def load_data(
        self,
        hotels_path: str,
        attractions_path: str,
        itineraries_path: str
    ):
        """Load and index travel data"""
        
        # Load hotels
        with open(hotels_path, 'r') as f:
            hotels_data = json.load(f)
        self._index_hotels(hotels_data.get('hotels', []))
        
        # Load attractions
        with open(attractions_path, 'r') as f:
            attractions_data = json.load(f)
        self._index_attractions(attractions_data.get('attractions', []))
        
        # Load itineraries
        with open(itineraries_path, 'r') as f:
            itineraries_data = json.load(f)
        # support both 'templates' and 'itineraries' keys
        self._index_itineraries(itineraries_data.get('templates') or itineraries_data.get('itineraries') or [])
        
        logger.info("Data indexed successfully")
    
    def _index_hotels(self, hotels: List[Dict]):
        """Index hotel data"""
        documents = []
        metadatas = []
        ids = []
        
        for hotel in hotels:
            # safe extraction with defaults
            name = hotel.get('name', '')
            loc = hotel.get('location', {})
            city = loc.get('city') or loc.get('district') or ''
            features = hotel.get('features', {})
            ftype = features.get('type', '')
            amenities = features.get('amenities') or []
            reviews = hotel.get('reviews', {})
            rating = reviews.get('avg_rating')
            pricing = hotel.get('pricing', {})
            price = pricing.get('base_price_inr')

            doc_text = f"""
            Hotel: {name}
            Location: {city}
            Type: {ftype}
            Rating: {rating if rating is not None else 'N/A'}/5
            Price: ₹{price if price is not None else 'N/A'} per night
            Amenities: {', '.join(amenities)}
            Best for: {', '.join(hotel.get('best_for') or [])}
            Description: {', '.join(reviews.get('common_praises') or [])}
            """

            documents.append(doc_text)
            metadatas.append({
                'id': hotel.get('id'),
                'name': name,
                'price': price,
                'rating': rating,
                'type': ftype
            })
            ids.append(hotel.get('id'))
        
        # Create embeddings and add to collection
        embeddings = self.embedder.encode(documents).tolist()
        
        self.hotels_collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def _index_attractions(self, attractions: List[Dict]):
        """Index attractions data"""
        documents = []
        metadatas = []
        ids = []
        
        for attr in attractions:
            name = attr.get('name', '')
            details = attr.get('details', {})
            atype = details.get('type', '')
            duration = details.get('duration_hours')
            entry_fee = details.get('entry_fee_inr')
            activities = []
            # support multiple possible structures
            if 'experience' in attr and isinstance(attr['experience'], dict):
                activities = attr['experience'].get('activities') or []
            else:
                activities = details.get('activities') or []
            best_months = attr.get('best_months') or details.get('best_months') or []

            doc_text = f"""
            Attraction: {name}
            Type: {atype}
            Activities: {', '.join(activities)}
            Entry Fee: ₹{entry_fee if entry_fee is not None else 'N/A'}
            Duration: {duration if duration is not None else 'N/A'} hours
            Best months: {', '.join(best_months)}
            """

            documents.append(doc_text)
            metadatas.append({
                'id': attr.get('id'),
                'name': name,
                'type': atype,
                'duration': duration
            })
            ids.append(attr.get('id'))
        
        embeddings = self.embedder.encode(documents).tolist()
        
        self.attractions_collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def _index_itineraries(self, itineraries: List[Dict]):
        """Index itinerary templates"""
        documents = []
        metadatas = []
        ids = []
        
        for itin in itineraries:
            name = itin.get('name') or ''
            duration = itin.get('duration_days') or itin.get('days') or None
            theme = itin.get('theme') or ', '.join(itin.get('interests') or [])
            target = itin.get('target_audience') or itin.get('interests') or []
            budget_avg = None
            if isinstance(itin.get('budget'), dict):
                budget_avg = itin['budget'].get('avg')
            else:
                budget_avg = itin.get('budget')
            destinations = []
            for d in (itin.get('days') or itin.get('route') or []):
                if isinstance(d, dict):
                    destinations.append(d.get('location') or d.get('place') or '')
                else:
                    destinations.append(str(d))

            doc_text = f"""
            Package: {name}
            Duration: {duration if duration is not None else 'N/A'} days
            Theme: {theme}
            Target: {', '.join(target)}
            Budget: ₹{budget_avg if budget_avg is not None else 'N/A'} (avg)
            Destinations: {', '.join(destinations)}
            Best months: {', '.join(itin.get('best_months') or [])}
            """

            documents.append(doc_text)
            metadatas.append({
                'id': itin.get('id'),
                'name': name,
                'duration': duration,
                'budget_avg': budget_avg,
                'theme': theme
            })
            ids.append(itin.get('id'))
        
        embeddings = self.embedder.encode(documents).tolist()
        
        self.itineraries_collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
    
    def search_hotels(
        self,
        query: str,
        filters: Optional[Dict] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Search hotels based on query"""
        
        query_embedding = self.embedder.encode(query).tolist()
        
        where_clause = {}
        if filters:
            # only include numeric filters to avoid passing None to ChromaDB
            max_price = filters.get('max_price')
            min_rating = filters.get('min_rating')
            if max_price is not None:
                try:
                    max_price_val = float(max_price)
                    where_clause['price'] = {'$lte': max_price_val}
                except (TypeError, ValueError):
                    logger.debug("Ignored non-numeric max_price filter: %s", max_price)
            if min_rating is not None:
                try:
                    min_rating_val = float(min_rating)
                    where_clause['rating'] = {'$gte': min_rating_val}
                except (TypeError, ValueError):
                    logger.debug("Ignored non-numeric min_rating filter: %s", min_rating)
        
        results = self.hotels_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause if where_clause else None
        )
        
        return self._format_results(results)
    
    def search_attractions(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """Search attractions"""
        
        query_embedding = self.embedder.encode(query).tolist()
        
        results = self.attractions_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return self._format_results(results)
    
    def search_itineraries(
        self,
        query: str,
        filters: Optional[Dict] = None,
        n_results: int = 3
    ) -> List[Dict]:
        """Search itinerary templates"""
        
        query_embedding = self.embedder.encode(query).tolist()
        
        # ChromaDB requires $and operator for multiple conditions
        where_clause = None
        if filters:
            conditions = []
            duration = filters.get('duration')
            max_budget = filters.get('max_budget')
            if duration is not None:
                try:
                    dur_val = int(duration)
                    conditions.append({'duration': {'$eq': dur_val}})
                except (TypeError, ValueError):
                    logger.debug("Ignored non-integer duration filter: %s", duration)
            if max_budget is not None:
                try:
                    budget_val = float(max_budget)
                    conditions.append({'budget_avg': {'$lte': budget_val}})
                except (TypeError, ValueError):
                    logger.debug("Ignored non-numeric max_budget filter: %s", max_budget)

            if len(conditions) == 1:
                where_clause = conditions[0]
            elif len(conditions) > 1:
                where_clause = {'$and': conditions}
        
        results = self.itineraries_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_clause
        )
        
        return self._format_results(results)
    
    def _format_results(self, results: Dict) -> List[Dict]:
        """Format ChromaDB results"""
        formatted = []
        
        if results['ids']:
            for i, doc_id in enumerate(results['ids'][0]):
                formatted.append({
                    'id': doc_id,
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                })
        
        return formatted

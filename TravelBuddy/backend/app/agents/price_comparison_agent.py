"""Price comparison agent to find best hotel deals"""

from typing import Dict, List, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(_name_)

class PriceComparisonAgent:
    """Agent for comparing hotel prices and finding deals"""
    
    def _init_(self, rag_pipeline):
        self.rag = rag_pipeline
    
    def find_deals(self, budget: int, location: Optional[str] = None, min_rating: float = 3.0) -> List[Dict]:
        """Find hotels within budget and rating constraints"""
        try:
            filters = {
                "max_price": budget,
                "min_rating": min_rating
            }
            if location:
                filters["location"] = location
            
            results = self.rag.search_hotels(
                query="",  # Empty query to get all results
                filters=filters,
                n_results=5
            )
            
            return [
                {
                    "name": r["metadata"].get("name", "Hotel"),
                    "price": r["metadata"].get("price", "N/A"),
                    "rating": r["metadata"].get("rating", "N/A"),
                    "location": r["metadata"].get("location", "N/A")
                }
                for r in results
            ]
        
        except Exception as e:
            logger.error(f"Error finding deals: {e}")
            return []
    
    def compare_hotels(
        self,
        location: str,
        check_in: str,
        check_out: str,
        filters: Optional[Dict] = None,
        n_results: int = 5
    ) -> List[Dict]:
        """Compare hotel prices for given dates and location"""
        try:
            # Validate dates
            try:
                start = datetime.strptime(check_in, "%Y-%m-%d").date()
                end = datetime.strptime(check_out, "%Y-%m-%d").date()
                if start < date.today() or end < start:
                    raise ValueError("Invalid dates")
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")
                return []
            
            # Default filters
            if filters is None:
                filters = {}
            filters["location"] = location
            
            results = self.rag.search_hotels(
                query=location,
                filters=filters,
                n_results=n_results
            )
            
            comparisons = []
            for r in results:
                hotel_info = r["metadata"]
                name = hotel_info.get("name", "Hotel")
                price = hotel_info.get("price", 0)
                
                # TODO: Add real-time price fetching from APIs
                comparisons.append({
                    "name": name,
                    "base_price": price,
                    "total_price": self._calculate_total_price(price, start, end),
                    "rating": hotel_info.get("rating", "N/A"),
                    "amenities": hotel_info.get("amenities", []),
                    "location": hotel_info.get("location", location),
                    "check_in": check_in,
                    "check_out": check_out,
                    "source": "internal",
                    "last_updated": datetime.now().isoformat()
                })
            
            return comparisons
        
        except Exception as e:
            logger.error(f"Error comparing hotels: {e}")
            return []
    
    def _calculate_total_price(self, base_price: float, check_in: date, check_out: date) -> float:
        """Calculate total price including taxes and fees"""
        nights = (check_out - check_in).days
        subtotal = base_price * nights
        
        # Example fees (customize based on your needs)
        taxes = subtotal * 0.18  # 18% GST
        service_fee = 500  # Fixed service fee
        
        total = subtotal + taxes + service_fee
        return round(total, 2)

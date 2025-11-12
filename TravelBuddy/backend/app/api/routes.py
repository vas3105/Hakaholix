from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import uuid

router = APIRouter()

# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    user_id: str
    context: Optional[Dict] = None
    language: Optional[str] = "en"
    session_id: Optional[str] = None
    location: Optional[Dict] = None  # User's current location if available
    preferences: Optional[Dict] = None  # Any specific preferences for this request
    previous_messages: Optional[List[Dict]] = None  # Conversation history

class ChatResponse(BaseModel):
    """Chat response model"""
    message: str
    intent: str
    entities: Dict
    recommendations: Dict[str, List[Dict]]  # Structured recommendations by type
    alternatives: Optional[Dict[str, List[Dict]]] = None  # Alternative options when exact matches aren't found
    status: Dict = {  # Response status information
        "success": True,
        "has_results": True,
        "error": None
    }
    context: Dict = {}  # Context carried forward
    suggestions: List[str] = []  # Suggested follow-up queries
    actions: List[Dict] = []  # Available actions user can take
    timestamp: str = None
    session_id: str = None
    confidence: float = 1.0  # Confidence score of the response
    fallback_options: Optional[Dict] = None  # Fallback options when no matches found
    metadata: Optional[Dict] = None  # Additional metadata

class HotelSearchRequest(BaseModel):
    query: str
    max_price: Optional[int] = None
    min_rating: Optional[float] = None
    limit: int = 5

class AttractionSearchRequest(BaseModel):
    query: str
    limit: int = 5

class ItineraryRequest(BaseModel):
    duration_days: int
    interests: List[str]
    budget: int
    start_date: Optional[str] = None
    preferences: Optional[Dict] = None

class BookingRequest(BaseModel):
    user_id: str
    item_type: str  # 'hotel' or 'attraction'
    item_id: str
    details: Dict

class PriceComparisonRequest(BaseModel):
    location: str
    check_in: str
    check_out: str
    filters: Optional[Dict] = None
    n_results: int = 5

# Dependency injection for services
def get_travel_agent():
    from app.main import travel_agent
    return travel_agent

def get_rag_pipeline():
    from app.main import rag_pipeline
    return rag_pipeline

def get_user_profile_service():
    from app.main import user_profile_service
    return user_profile_service

# Chat endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    agent = Depends(get_travel_agent),
    profile_service = Depends(get_user_profile_service)
):
    """
    Handle chat messages and generate contextual responses
    
    Parameters:
    - message: The user's message text
    - user_id: Unique identifier for the user
    - context: Optional context from previous interactions
    - language: Preferred language for response (default: "en")
    - session_id: Optional session identifier for conversation tracking
    - location: User's current location if available
    - preferences: Any specific preferences for this request
    - previous_messages: Conversation history for context
    
    Returns a ChatResponse with:
    - Processed message response
    - Detected intent and entities
    - Relevant recommendations
    - Context for next interaction
    - Suggested follow-up queries
    - Available actions
    - Metadata and confidence scores
    """
    try:
        # Get user profile for personalization
        profile = profile_service.get_profile(request.user_id)
        
        # Process the query with full context
        response = agent.process_query(
            user_message=request.message,
            user_id=request.user_id,
            context={
                "profile": profile,
                "session": request.session_id,
                "language": request.language,
                "location": request.location,
                "preferences": request.preferences,
                "history": request.previous_messages,
                "provided_context": request.context
            }
        )
        
        # Add timestamp and session info
        response.update({
            "timestamp": datetime.now().isoformat(),
            "session_id": request.session_id or response.get("session_id", str(uuid.uuid4())),
            "metadata": {
                "user_location": request.location,
                "language": request.language,
                "profile_segments": profile.get("segments", []),
                "response_time": datetime.now().isoformat()
            }
        })
        if not response.get("message"):
            response["message"] = "I'm here! How can I help you plan your Kerala trip today?"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Hotel endpoints
@router.post("/hotels/search")
async def search_hotels(
    request: HotelSearchRequest,
    rag = Depends(get_rag_pipeline)
):
    """Search for hotels"""
    try:
        filters = {}
        if request.max_price:
            filters['max_price'] = request.max_price
        if request.min_rating:
            filters['min_rating'] = request.min_rating
        
        results = rag.search_hotels(
            request.query,
            filters=filters,
            n_results=request.limit
        )
        
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hotels/{hotel_id}")
async def get_hotel_details(
    hotel_id: str,
    rag = Depends(get_rag_pipeline)
):
    """Get specific hotel details"""
    try:
        results = rag.search_hotels(hotel_id, n_results=1)
        if not results:
            raise HTTPException(status_code=404, detail="Hotel not found")
        return results[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Attraction endpoints
@router.post("/attractions/search")
async def search_attractions(
    request: AttractionSearchRequest,
    rag = Depends(get_rag_pipeline)
):
    """Search for attractions"""
    try:
        results = rag.search_attractions(
            request.query,
            n_results=request.limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/attractions/{attraction_id}")
async def get_attraction_details(
    attraction_id: str,
    rag = Depends(get_rag_pipeline)
):
    """Get specific attraction details"""
    try:
        results = rag.search_attractions(attraction_id, n_results=1)
        if not results:
            raise HTTPException(status_code=404, detail="Attraction not found")
        return results[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Itinerary endpoints
@router.post("/itinerary/generate")
async def generate_itinerary(
    request: ItineraryRequest,
    agent = Depends(get_travel_agent)
):
    """Generate a custom itinerary"""
    try:
        itinerary = agent.itinerary_agent.generate_itinerary(
            duration_days=request.duration_days,
            interests=request.interests,
            budget=request.budget,
            start_date=request.start_date,
            preferences=request.preferences
        )
        return itinerary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/itinerary/optimize")
async def optimize_itinerary(
    itinerary: Dict,
    optimization_goal: str = 'cost',
    agent = Depends(get_travel_agent)
):
    """Optimize an existing itinerary"""
    try:
        optimized = agent.itinerary_agent.optimize_itinerary(
            itinerary,
            optimization_goal
        )
        return optimized
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/itinerary/export")
async def export_itinerary(
    itinerary: Dict,
    format: str = 'json',
    agent = Depends(get_travel_agent)
):
    """Export itinerary in different formats"""
    try:
        exported = agent.itinerary_agent.export_itinerary(itinerary, format)
        return {"data": exported, "format": format}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Booking endpoints
@router.post("/booking/initiate")
async def initiate_booking(
    request: BookingRequest,
    agent = Depends(get_travel_agent)
):
    """Initiate a booking"""
    try:
        result = agent.booking_agent.initiate_booking(
            user_id=request.user_id,
            item_type=request.item_type,
            item_id=request.item_id,
            details=request.details
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/booking/{booking_id}/confirm")
async def confirm_booking(
    booking_id: str,
    agent = Depends(get_travel_agent)
):
    """Confirm a booking"""
    try:
        result = agent.booking_agent.confirm_booking(booking_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/booking/{booking_id}")
async def cancel_booking(
    booking_id: str,
    agent = Depends(get_travel_agent)
):
    """Cancel a booking"""
    try:
        result = agent.booking_agent.cancel_booking(booking_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/booking/{booking_id}")
async def get_booking(
    booking_id: str,
    agent = Depends(get_travel_agent)
):
    """Get booking details"""
    try:
        booking = agent.booking_agent.get_booking_details(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bookings/user/{user_id}")
async def get_user_bookings(
    user_id: str,
    agent = Depends(get_travel_agent)
):
    """Get all bookings for a user"""
    try:
        bookings = agent.booking_agent.get_user_bookings(user_id)
        return {"bookings": bookings, "count": len(bookings)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Price comparison endpoints
@router.post("/prices/compare")
async def compare_prices(
    request: PriceComparisonRequest,
    agent = Depends(get_travel_agent)
):
    """Compare hotel prices"""
    try:
        comparison = agent.price_comparison_agent.compare_hotels(
            location=request.location,
            check_in=request.check_in,
            check_out=request.check_out,
            filters=request.filters,
            n_results=request.n_results
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/prices/deals")
async def get_deals(
    budget: int,
    location: Optional[str] = None,
    min_rating: float = 3.0,
    agent = Depends(get_travel_agent)
):
    """Find hotel deals within budget"""
    try:
        deals = agent.price_comparison_agent.find_deals(
            budget=budget,
            location=location,
            min_rating=min_rating
        )
        return {"deals": deals, "count": len(deals)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# User profile endpoints
@router.get("/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    profile_service = Depends(get_user_profile_service)
):
    """Get user profile"""
    try:
        profile = profile_service.get_profile(user_id)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile/{user_id}")
async def update_user_profile(
    user_id: str,
    updates: Dict,
    profile_service = Depends(get_user_profile_service)
):
    """Update user profile"""
    try:
        profile_service.update_profile(user_id, updates)
        return {"success": True, "message": "Profile updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}/recommendations")
async def get_user_recommendations(
    user_id: str,
    profile_service = Depends(get_user_profile_service)
):
    """Get personalized recommendations"""
    try:
        recommendations = profile_service.get_recommendations(user_id)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}/preferences")
async def get_user_preferences(
    user_id: str,
    profile_service = Depends(get_user_profile_service)
):
    """Get all user preferences"""
    try:
        prefs = profile_service.get_preferences(user_id)
        return {
            "user_embeddings": prefs.user_embeddings.get(user_id, {}),
            "preference_vectors": prefs.preference_vectors.get(user_id, {}),
            "seasonal_preferences": prefs.seasonal_preferences.get(user_id, {}),
            "travel_group_preferences": prefs.travel_group_preferences.get(user_id, {}),
            "amenity_preferences": prefs.amenity_preferences.get(user_id, {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

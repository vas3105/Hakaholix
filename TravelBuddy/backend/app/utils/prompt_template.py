"""Prompt templates for LLM interactions."""

from typing import List, Dict, Optional, Final

# ---------------------------------------------------
# 🧠 System + Base Prompts
# ---------------------------------------------------

SYSTEM_PROMPT: Final[str] = """You are an intelligent travel assistant specializing in personalized Kerala tourism experiences.
Your role is to deeply understand user preferences and provide highly customized travel recommendations.

Core capabilities:
1. Personalized Planning:
   - Understand and adapt to user's travel style
   - Consider past preferences and experiences
   - Adjust recommendations based on feedback

2. Smart Recommendations:
   - Hotels matching exact preferences and constraints
   - Activities aligned with interests and energy levels
   - Restaurants catering to dietary needs and cuisine preferences

3. Dynamic Optimization:
   - Real-time budget optimization
   - Weather-aware activity planning
   - Crowd-sensitive scheduling

4. Contextual Understanding:
   - Remember past conversations
   - Build on previous interactions
   - Consider travel group dynamics

Style Guide:
- Be conversational yet professional
- Provide specific, actionable recommendations
- Explain the reasoning behind suggestions
- Anticipate needs and potential issues
- Offer alternatives when appropriate

Focus on creating experiences that are:
1. Personally meaningful
2. Logistically optimized
3. Budget-conscious
4. Time-efficient
5. Memory-worthy"""

INTENT_CLASSIFICATION_PROMPT: Final[str] = """Classify the user's intent from the following message:

User message: {message}

Available intents:
- hotel_search
- attraction_search
- itinerary_planning
- booking
- price_inquiry
- general_info
- greeting
- other

Respond with ONLY the intent name, nothing else."""

ENTITY_EXTRACTION_PROMPT: Final[str] = """Extract relevant travel entities from the user's message:

User message: {message}

Extract the following if present:
- location
- duration
- budget
- interests
- dates
- number_of_people

Respond ONLY with valid JSON format:
{{
  "location": [],
  "duration": "",
  "budget": null,
  "interests": [],
  "dates": {{}},
  "number_of_people": null
}}"""

HOTEL_RECOMMENDATION_PROMPT: Final[str] = """Based on the user's requirements, provide hotel recommendations:

User requirements:
{requirements}

Available hotels:
{hotels}

Provide a natural language response recommending 2–3 hotels that best match the requirements.
Include price, location, and why you're recommending them.
Keep the response under 150 words."""

ITINERARY_GENERATION_PROMPT: Final[str] = """Create a detailed day-by-day itinerary:

Duration: {duration} days
Budget: ₹{budget}
Interests: {interests}
Retrieved attractions:
{attractions}

Generate a structured itinerary with:
- Daily activities
- Meals
- Transport tips
- Budget breakdown
"""

RESPONSE_GENERATION_PROMPT: Final[str] = """Generate a helpful response to the user:

User query: {query}
Intent: {intent}
Retrieved context: {context}
User profile: {profile}

Requirements:
1. Be conversational and friendly
2. Use retrieved context for specific recommendations
3. Keep under 200 words
4. Include actionable suggestions
5. End with a question if appropriate

Response:"""

CONVERSATION_SUMMARY_PROMPT: Final[str] = """Summarize the key points from this conversation:

Conversation history:
{history}

Provide a short summary (3–4 sentences) of:
1. What the user wants
2. Preferences mentioned
3. Decisions made
4. Next steps
"""

PRICE_COMPARISON_PROMPT: Final[str] = """Compare these hotels and provide recommendations:

Hotels data:
{hotels_data}

User budget: ₹{budget}
User preferences: {preferences}

Provide:
- Best value option
- Budget-friendly option
- Luxury option
Include short explanations.
"""

ERROR_RESPONSE_PROMPT: Final[str] = """The system encountered an issue.

Error type: {error_type}
User query: {query}

Generate a friendly message that:
1. Acknowledges the issue
2. Suggests an alternative action
3. Stays positive and brief (2–3 sentences)."""

# ---------------------------------------------------
# 🧩 Formatting Functions
# ---------------------------------------------------

def format_system_prompt(role: str = "travel_assistant") -> str:
    """Return system prompt by role."""
    prompts = {
        "travel_assistant": SYSTEM_PROMPT,
        "booking_specialist": "You are a booking specialist helping users complete their travel bookings.",
        "price_advisor": "You are a price advisor helping users find the best deals."
    }
    return prompts.get(role, SYSTEM_PROMPT)


def format_chat_prompt(
    user_message: str,
    context: Optional[str] = "",
    history: Optional[List[Dict[str, str]]] = None
) -> str:
    """Format a complete chat prompt."""
    prompt = format_system_prompt()

    if history:
        prompt += "\n\nPrevious conversation:\n"
        for msg in history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt += f"{role.capitalize()}: {content}\n"

    if context:
        prompt += f"\n\nRelevant context:\n{context}\n"

    prompt += f"\n\nUser: {user_message}\nAssistant:"
    return prompt


def format_intent_prompt(message: str) -> str:
    """Format intent classification prompt."""
    return INTENT_CLASSIFICATION_PROMPT.format(message=message)


def format_entity_extraction_prompt(message: str) -> str:
    """Format entity extraction prompt."""
    return ENTITY_EXTRACTION_PROMPT.format(message=message)


def format_recommendation_prompt(
    requirements: Dict,
    results: List[Dict],
    rec_type: str = "hotel"
) -> str:
    """Format hotel or other recommendation prompt."""
    if rec_type == "hotel" and results:
        hotels_text = "\n\n".join([
            f"Hotel: {r.get('metadata', {}).get('name', 'Unknown')}\n"
            f"Description: {r.get('document', '')[:200]}"
            for r in results[:3]
        ])
        return HOTEL_RECOMMENDATION_PROMPT.format(
            requirements=json_safe_str(requirements),
            hotels=hotels_text
        )
    return "No recommendations found."


def format_itinerary_prompt(
    duration: int,
    budget: int,
    interests: List[str],
    attractions: List[Dict]
) -> str:
    """Format itinerary generation prompt."""
    attractions_text = "\n".join([
        f"- {a.get('metadata', {}).get('name', 'Unknown')}: {a.get('document', '')[:100]}"
        for a in attractions[:10]
    ])
    return ITINERARY_GENERATION_PROMPT.format(
        duration=duration,
        budget=budget,
        interests=", ".join(interests),
        attractions=attractions_text
    )

# Utility to safely stringify dicts
def json_safe_str(data) -> str:
    """Convert dict safely to string (avoid crashes)."""
    try:
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        return str(data)

"""Main travel agent orchestrating all sub-agents with intelligent personalization and real-time context"""

from typing import Dict, List, Optional
from datetime import datetime
import logging
import json
import requests  # ✅ added for weather API
import re
import os

from app.utils.prompt_templates import (
    SYSTEM_PROMPT,
    format_chat_prompt,
)
from app.utils.data_processing import (
    parse_duration,
    parse_budget,
    extract_locations,
    extract_interests,
    parse_number_of_people
)
from app.models.user_preferences import UserPreferences
from app.config import settings
from app.agents.itinerary_agent import ItineraryAgent

logger = logging.getLogger(_name_)

class TravelAgent:
    """Main conversational agent for travel planning"""
    
    def _init_(self, llm_handler, rag_pipeline, user_profile_service):
        self.llm = llm_handler
        self.rag = rag_pipeline
        self.user_profile_service = user_profile_service
        
        self.user_preferences = UserPreferences("all-MiniLM-L6-v2")
        # default location from config
        self.DEFAULT_LOCATION = getattr(settings, 'DEFAULT_LOCATION', 'Kerala')
        
        self.booking_agent = None
        self.price_comparison_agent = None
        self.itinerary_agent = None
        
        self.conversations = {}
        self.user_contexts = {}
        self.recent_recommendations = {}
        
        # ✅ Environment keys for weather
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
        
    # ----------------------------------------------------------------
    # 🧠 MAIN PROCESSING PIPELINE
    # ----------------------------------------------------------------
    def process_query(self, user_message: str, user_id: str, context: Optional[Dict] = None) -> Dict:
        """Process user query and generate response"""
        try:
            if user_id not in self.conversations:
                self.conversations[user_id] = []

            user_profile = self.user_profile_service.get_profile(user_id)
            intent = self._classify_intent(user_message)
            logger.info(f"Classified intent: {intent}")

            entities = self._extract_entities(user_message)
            logger.info(f"Extracted entities: {entities}")

            # ✅ Add real-time weather if city is mentioned
            locs = entities.get("location") or []
            if locs:
                city = locs[0]
                weather_data = self._get_weather_info(city)
                emergency_contacts = self._get_emergency_contacts(city)
            else:
                weather_data = None
                emergency_contacts = None

            # Route intent
            if intent == 'hotel_search':
                response = self._handle_hotel_search(user_message, entities, user_profile)
            elif intent == 'attraction_search':
                response = self._handle_attraction_search(user_message, entities)
            elif intent == 'itinerary_planning':
                response = self._handle_itinerary_planning(user_message, entities, user_profile)
            elif intent == 'booking':
                response = self._handle_booking(user_message, entities, user_id)
            elif intent == 'price_inquiry':
                response = self._handle_price_inquiry(user_message, entities)
            elif intent == 'general_info':
                response = self._handle_general_info(user_message)
            elif intent == 'greeting':
                response = self._handle_greeting(user_message, user_profile)
            else:
                response = self._handle_general_query(user_message, user_profile)

            # ✅ Inject weather/emergency info into any reply
            if weather_data:
                response["weather"] = weather_data
            if emergency_contacts:
                response["emergency_contacts"] = emergency_contacts

            # Update logs and conversation
            self.conversations[user_id].append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            self.conversations[user_id].append({
                'role': 'assistant',
                'content': response['message'],
                'timestamp': datetime.now().isoformat()
            })

            # Limit chat history
            self.conversations[user_id] = self.conversations[user_id][-20:]

            # Update profile
            self.user_profile_service.update_profile(user_id, {
                'search_query': user_message,
                'interests': entities.get('interests', [])
            })

            # Add meta
            response['intent'] = intent
            response['entities'] = entities
            response['timestamp'] = datetime.now().isoformat()
            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "message": "Oops! I ran into a problem processing that. Could you try rephrasing?",
                "intent": "error",
                "entities": {},
                "timestamp": datetime.now().isoformat()
            }

    # ----------------------------------------------------------------
    # 🔍 INTENT & ENTITY DETECTION
    # ----------------------------------------------------------------
    def _classify_intent(self, message: str) -> str:
        msg = message.lower()
        if any(x in msg for x in ["hotel", "stay", "resort"]):
            return "hotel_search"
        if any(x in msg for x in ["attraction", "visit", "see"]):
            return "attraction_search"
        if any(x in msg for x in ["itinerary", "plan", "trip", "days"]):
            return "itinerary_planning"
        if any(x in msg for x in ["book", "reserve", "booking"]):
            return "booking"
        if any(x in msg for x in ["price", "cost", "budget"]):
            return "price_inquiry"
        if any(x in msg for x in ["weather", "climate"]):
            return "general_info"
        if any(x in msg for x in ["hi", "hello", "hey", "greetings"]):
            return "greeting"
        return "other"

    def _extract_entities(self, message: str) -> Dict:
        return {
            "location": extract_locations(message),
            "duration": parse_duration(message),
            "budget": parse_budget(message),
            "interests": extract_interests(message),
            "number_of_people": parse_number_of_people(message)
        }

    # ----------------------------------------------------------------
    # 🤖 GREETING HANDLER (Granite)
    # ----------------------------------------------------------------
    def _handle_greeting(self, message: str, profile: Dict) -> Dict:
        """
        Handle greeting messages using Granite for natural tone,
        but differentiate between new and returning users.
        """

        user_name = profile.get("name", "there")
        prev_bookings = len(profile.get("bookings", []))
        is_returning_user = prev_bookings > 0 or len(self.conversations.get(profile.get("user_id", ""), [])) > 2

        if is_returning_user:
            tone_instruction = (
                "The user has interacted before. Greet them like an old friend coming back. "
                "Use a warm, familiar tone (but don't explicitly say 'back' unless natural)."
            )
        else:
            tone_instruction = (
                "This is the user's first interaction. Greet them like a new guest visiting Kerala for the first time. "
                "Be friendly, welcoming, and mention Kerala briefly."
            )

        prompt = f"""
    You are a friendly Kerala travel assistant.
    {tone_instruction}

    User name: {user_name}
    User message: "{message}"

    Your reply:
    - Must be 1–2 sentences max.
    - Should sound like a real person (no robotic tone).
    - Avoid repeating system instructions or adding 'Assistant:'.
    - Avoid saying 'back' unless clearly appropriate.

    Assistant:
    """

        try:
            # prefer safe generation wrapper
            if hasattr(self.llm, 'generate_safe'):
                reply = self.llm.generate_safe(
                    prompt,
                    max_tokens=80,
                    temperature=0.6
                ).strip()
            else:
                reply = self.llm.generate(prompt, max_tokens=80).strip()

            # Ensure reply is human and mentions capabilities
            if not reply or "you are a" in reply.lower():
                reply = (
                    f"Hi {user_name}! I'm the Kerala Travel Assistant — your travel agent for Kerala. "
                    "I can find hotels, suggest attractions, and create itineraries for any number of days. "
                    "How can I help you today?"
                )

        except Exception as e:
            logger.error(f"Granite greeting error: {e}")
            reply = (
                f"Hi {user_name}! I'm the Kerala Travel Assistant — a travel agent assistant. "
                "Tell me how many days you'd like to visit (e.g. 2, 3, 5) or ask for hotels/attractions."
            )

        return {
            "message": reply,
            "recommendations": {
                "quick_actions": [
                    {"label": "Search for hotels", "action": "search_hotels"},
                    {"label": "Find tourist attractions", "action": "find_attractions"},
                    {"label": "Plan an itinerary", "action": "plan_itinerary"},
                    {"label": "Check weather", "action": "check_weather"}
                ]
            }
        }


    # ----------------------------------------------------------------
    # 🌦 WEATHER HANDLER (REAL-TIME API)
    # ----------------------------------------------------------------
    def _get_weather_info(self, city: str) -> Optional[Dict]:
        """Fetch real-time weather using OpenWeatherMap API"""
        try:
            if not self.WEATHER_API_KEY:
                logger.warning("Weather API key not found")
                return None
                
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.WEATHER_API_KEY}&units=metric"
            res = requests.get(url, timeout=5)
            data = res.json()
            if res.status_code != 200:
                return None
            return {
                "city": city,
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "condition": data["weather"][0]["description"].capitalize(),
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
        except Exception as e:
            logger.error(f"Weather API failed for {city}: {e}")
            return None

    # ----------------------------------------------------------------
    # 🚨 EMERGENCY CONTACTS
    # ----------------------------------------------------------------
    def _get_emergency_contacts(self, city: str) -> Dict:
        """Return emergency contact numbers based on city"""
        city_lower = city.lower()
        default = {
            "police": "100",
            "ambulance": "108",
            "fire": "101",
            "tourist helpline": "1363",
            "women helpline": "1091"
        }

        kerala_contacts = {
            "kochi": {"nearest hospital": "Ernakulam Medical Centre – 0484 290 7000"},
            "thiruvananthapuram": {"nearest hospital": "KIMS Health – 0471 294 1000"},
            "munnar": {"nearest hospital": "Tata General Hospital – 04865 230 444"},
            "wayanad": {"nearest hospital": "Assumption Hospital – 04936 260 421"},
            "alleppey": {"nearest hospital": "SD Hospital – 0477 223 0250"}
        }

        extra = kerala_contacts.get(city_lower, {})
        return {**default, **extra}

    # ----------------------------------------------------------------
    # 🏨 HOTEL HANDLER
    # ----------------------------------------------------------------
    def _handle_hotel_search(self, message: str, entities: Dict, profile: Dict) -> Dict:
        locs = entities.get("location") or []
        location = locs[0] if locs else self.DEFAULT_LOCATION
        results = self.rag.search_hotels(location, n_results=3)

        if not results:
            return {"message": f"Couldn't find any hotels in {location}.", "recommendations": {}}

        hotels = [
            {"name": r["metadata"].get("name", "Hotel"), "price": r["metadata"].get("price", "N/A")}
            for r in results
        ]
        return {
            "message": f"Here are some hotels you might like in {location}:",
            "recommendations": {"hotels": hotels}
        }

    # ----------------------------------------------------------------
    # 🎯 ATTRACTION HANDLER
    # ----------------------------------------------------------------
    def _handle_attraction_search(self, message: str, entities: Dict) -> Dict:
        locs = entities.get("location") or []
        location = locs[0] if locs else self.DEFAULT_LOCATION
        results = self.rag.search_attractions(location, n_results=3)

        if not results:
            return {"message": f"Couldn't find attractions in {location}.", "recommendations": {}}

        attractions = [
            {"name": r["metadata"].get("name", "Attraction"), "description": r["document"][:100] + "..."}
            for r in results
        ]
        return {
            "message": f"Here are some must-visit attractions in {location}:",
            "recommendations": {"attractions": attractions}
        }

    # ----------------------------------------------------------------
    # 🧭 ITINERARY HANDLER
    # ----------------------------------------------------------------
    def _handle_itinerary_planning(self, message: str, entities: Dict, profile: Dict) -> Dict:
        duration = entities.get("duration") or 0
        # Try to extract numeric day counts from the message if parser failed
        if not duration or (isinstance(duration, int) and duration <= 0):
            m = re.search(r"(\d+)\s*(?:-?day|days|day|nights)?", message)
            if m:
                try:
                    duration = int(m.group(1))
                except Exception:
                    duration = 0

        # default to 3 days if still unknown
        if not duration or duration <= 0:
            duration = 3
        locs = entities.get("location") or []
        location = locs[0] if locs else self.DEFAULT_LOCATION
        interests = entities.get("interests", [])
        budget = entities.get("budget", 10000)

        # If itinerary agent available, prefer it. Otherwise ask LLM to draft a simple itinerary.
        try:
            if self.itinerary_agent:
                itinerary = self.itinerary_agent.generate_itinerary(
                    duration_days=duration,
                    interests=interests,
                    budget=budget,
                    preferences={"location": location}
                )
                if itinerary:
                    return {
                        "message": f"Here's a {duration}-day itinerary for {location}:",
                        "recommendations": {"itinerary": itinerary}
                    }

            # Fallback: ask LLM to generate a human-friendly itinerary
            llm_prompt = (
                f"You are a helpful Kerala travel agent. Create a concise, day-by-day {duration}-day "
                f"itinerary for {location}. Prioritize popular places, short travel times, and include 2-3 activities per day. "
                f"Return a JSON array of days with title and activities. Keep the language friendly and actionable."
            )

            if hasattr(self.llm, 'generate_safe'):
                draft = self.llm.generate_safe(llm_prompt, max_tokens=400, temperature=0.6)
            else:
                draft = self.llm.generate(llm_prompt, max_tokens=400)

            # Try to parse JSON from draft; if not JSON, return as text
            try:
                parsed = None
                # attempt to find first JSON array/object in text
                jmatch = re.search(r"(\{.\}|\[.\])", draft, re.S)
                if jmatch:
                    parsed = json.loads(jmatch.group(1))
                else:
                    # build a simple structure
                    parsed = [{"day": i+1, "plan": line.strip()} for i, line in enumerate(draft.splitlines()) if line.strip()][:duration]

                return {
                    "message": f"Here's a {duration}-day itinerary for {location} (generated by assistant):",
                    "recommendations": {"itinerary": parsed}
                }

            except Exception:
                # return plain text if parsing failed
                return {
                    "message": f"Here's a {duration}-day itinerary for {location}:\n" + draft,
                    "recommendations": {"itinerary": draft}
                }

        except Exception as e:
            logger.error(f"Itinerary generation failed: {e}")
            return {
                "message": "Sorry, I couldn't create an itinerary right now. Try specifying a number of days like '2-day' or '5-day'.",
                "recommendations": {}
            }

    # ----------------------------------------------------------------
    # 💰 PRICE HANDLER
    # ----------------------------------------------------------------
    def _handle_price_inquiry(self, message: str, entities: Dict) -> Dict:
        budget = entities.get("budget", 10000)
        deals = self.price_comparison_agent.find_deals(budget=budget)
        if not deals:
            return {"message": "Couldn't find hotel deals right now.", "recommendations": {}}

        return {
            "message": f"Here are a few hotels within your ₹{budget} budget:",
            "recommendations": {"deals": deals}
        }

    # ----------------------------------------------------------------
    # 📘 GENERAL INFO HANDLER
    # ----------------------------------------------------------------
    def _handle_general_info(self, message: str) -> Dict:
        prompt = f"You are a Kerala travel assistant. Provide a concise, friendly answer: {message}"
        if hasattr(self.llm, 'generate_safe'):
            reply = self.llm.generate_safe(prompt, max_tokens=200, temperature=0.5)
        else:
            reply = self.llm.generate(prompt, max_tokens=200)
        return {"message": reply, "recommendations": {}}

    # ----------------------------------------------------------------
    # 🧩 BOOKING HANDLER
    # ----------------------------------------------------------------
    def _handle_booking(self, message: str, entities: Dict, user_id: str) -> Dict:
        details = {
            "check_in": "2025-12-10",
            "check_out": "2025-12-12",
            "guests": 2,
            "rooms": 1
        }
        result = self.booking_agent.initiate_booking(user_id, "hotel", "H001", details)
        return {"message": result["message"], "recommendations": {"booking": result}}

    # ----------------------------------------------------------------
    # 🧠 GENERAL QUERY (fallback)
    # ----------------------------------------------------------------
    def _handle_general_query(self, message: str, profile: Dict) -> Dict:
        # Try a safe LLM call first, else provide a helpful fallback
        prompt = (
            "You are a helpful Kerala travel assistant. If the user asks something you can't answer, "
            "be honest and offer alternatives (search hotels, create itinerary, check weather).\nUser: " + message
        )
        if hasattr(self.llm, 'generate_safe'):
            reply = self.llm.generate_safe(prompt, max_tokens=240, temperature=0.6)
        else:
            reply = self.llm.generate(prompt, max_tokens=240)

        # If reply looks like a failure, return structured guidance
        if not reply or any(x in reply.lower() for x in ["i don't know", "can't", "unable"]):
            return {
                "message": "I don't have a direct answer for that, but I can help with hotels, attractions, or building an itinerary — what would you like?",
                "recommendations": {
                    "quick_actions": [
                        {"label": "Search hotels", "action": "search_hotels"},
                        {"label": "Create itinerary", "action": "plan_itinerary"},
                        {"label": "Check weather", "action": "check_weather"}
                    ]
                }
            }

        return {"message": reply, "recommendations": {}}

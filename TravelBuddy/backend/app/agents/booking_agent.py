from typing import Dict, List, Optional
from datetime import datetime
import logging
import requests
import os

logger = logging.getLogger(_name_)

class BookingAgent:
    """Handles hotel and attraction booking logic with real-time context"""

    def _init_(self, rag_pipeline, user_profile_service):
        self.rag_pipeline = rag_pipeline
        self.user_profile_service = user_profile_service
        self.pending_bookings = {}

        # ✅ API keys from environment
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "c540902e3fac5160482f15da30f46ea3")
        self.SKYSCANNER_API_KEY = os.getenv("SKYSCANNER_API_KEY", "afe62c8c024412fab44fd7dd57cab65c")

    # ---------------------------------------------------------------------
    # 🧾 BOOKING WORKFLOW
    # ---------------------------------------------------------------------
    def initiate_booking(self, user_id: str, item_type: str, item_id: str, details: Dict) -> Dict:
        """Initiate a booking request"""
        booking_id = f"{user_id}{item_type}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        booking_request = {
            "booking_id": booking_id,
            "user_id": user_id,
            "item_type": item_type,
            "item_id": item_id,
            "details": details,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        self.pending_bookings[booking_id] = booking_request
        logger.info(f"Booking initiated: {booking_id}")

        return {
            "success": True,
            "booking_id": booking_id,
            "message": "Booking request created. Please confirm details.",
            "booking_details": booking_request,
        }

    def confirm_booking(self, booking_id: str) -> Dict:
        """Confirm and finalize booking"""
        if booking_id not in self.pending_bookings:
            return {"success": False, "message": "Booking not found"}

        booking = self.pending_bookings[booking_id]
        booking["status"] = "confirmed"
        booking["confirmed_at"] = datetime.now().isoformat()

        # ✅ Fetch contextual info (weather + emergency)
        city = booking["details"].get("city") or "Kerala"
        weather = self._get_weather_info(city)
        emergency = self._get_emergency_contacts(city)

        # Save to user profile
        self.user_profile_service.add_booking(booking["user_id"], booking)
        del self.pending_bookings[booking_id]

        logger.info(f"Booking confirmed: {booking_id}")

        return {
            "success": True,
            "booking_id": booking_id,
            "message": f"Booking confirmed successfully for {city}!",
            "booking": booking,
            "weather": weather,
            "emergency_contacts": emergency,
        }

    def cancel_booking(self, booking_id: str) -> Dict:
        """Cancel a booking"""
        if booking_id in self.pending_bookings:
            del self.pending_bookings[booking_id]
            return {"success": True, "message": "Booking cancelled"}
        return {"success": False, "message": "Booking not found"}

    def get_booking_details(self, booking_id: str) -> Optional[Dict]:
        """Get booking details"""
        return self.pending_bookings.get(booking_id)

    def get_user_bookings(self, user_id: str) -> List[Dict]:
        """Get all bookings for a user"""
        profile = self.user_profile_service.get_profile(user_id)
        return profile.get("bookings", [])

    # ---------------------------------------------------------------------
    # ✅ VALIDATION AND COST CALCULATION
    # ---------------------------------------------------------------------
    def validate_booking_details(self, item_type: str, details: Dict) -> Dict:
        """Validate booking details"""
        errors = []

        if item_type == "hotel":
            required = ["check_in", "check_out", "guests", "rooms", "city"]
            for field in required:
                if field not in details:
                    errors.append(f"Missing required field: {field}")

            if "check_in" in details and "check_out" in details:
                try:
                    check_in = datetime.fromisoformat(details["check_in"])
                    check_out = datetime.fromisoformat(details["check_out"])
                    if check_in >= check_out:
                        errors.append("Check-out must be after check-in")
                    if check_in < datetime.now():
                        errors.append("Check-in date cannot be in the past")
                except ValueError:
                    errors.append("Invalid date format — use YYYY-MM-DD")

        elif item_type == "attraction":
            required = ["visit_date", "visitors", "city"]
            for field in required:
                if field not in details:
                    errors.append(f"Missing required field: {field}")

        return {"valid": len(errors) == 0, "errors": errors}

    def calculate_booking_cost(self, item_type: str, item_id: str, details: Dict) -> Dict:
        """Calculate total booking cost"""
        if item_type == "hotel":
            results = self.rag_pipeline.search_hotels(item_id, n_results=1)
        elif item_type == "attraction":
            results = self.rag_pipeline.search_attractions(item_id, n_results=1)
        else:
            return {"error": "Invalid item type"}

        if not results:
            return {"error": "Item not found"}

        base_price = results[0]["metadata"].get("price", 0)

        if item_type == "hotel":
            check_in = datetime.fromisoformat(details["check_in"])
            check_out = datetime.fromisoformat(details["check_out"])
            nights = (check_out - check_in).days
            rooms = details.get("rooms", 1)
            subtotal = base_price * nights * rooms
            taxes = subtotal * 0.12
            total = subtotal + taxes
            return {
                "base_price": base_price,
                "nights": nights,
                "rooms": rooms,
                "subtotal": subtotal,
                "taxes": taxes,
                "total": total,
                "currency": "INR",
            }

        elif item_type == "attraction":
            visitors = details.get("visitors", 1)
            subtotal = base_price * visitors
            taxes = subtotal * 0.05
            total = subtotal + taxes
            return {
                "base_price": base_price,
                "visitors": visitors,
                "subtotal": subtotal,
                "taxes": taxes,
                "total": total,
                "currency": "INR",
            }

    # ---------------------------------------------------------------------
    # 🌦 WEATHER & 🚨 EMERGENCY HELPERS
    # ---------------------------------------------------------------------
    def _get_weather_info(self, city: str) -> Optional[Dict]:
        """Fetch live weather for the city"""
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.WEATHER_API_KEY}&units=metric"
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                return None
            data = res.json()
            return {
                "city": city,
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "condition": data["weather"][0]["description"].capitalize(),
                "humidity": data["main"]["humidity"],
            }
        except Exception as e:
            logger.error(f"Weather fetch failed for {city}: {e}")
            return None

    def _get_emergency_contacts(self, city: str) -> Dict:
        """Return emergency contact numbers based on city"""
        base_contacts = {
            "police": "100",
            "ambulance": "108",
            "fire": "101",
            "tourist helpline": "1363",
            "women helpline": "1091",
        }
        kerala_specific = {
            "kochi": {"nearest hospital": "Ernakulam Medical Centre – 0484 290 7000"},
            "thiruvananthapuram": {"nearest hospital": "KIMS Health – 0471 294 1000"},
            "munnar": {"nearest hospital": "Tata General Hospital – 04865 230 444"},
            "wayanad": {"nearest hospital": "Assumption Hospital – 04936 260 421"},
            "alleppey": {"nearest hospital": "SD Hospital – 0477 223 0250"},
        }
        city_key = city.lower()
        return {**base_contacts, **kerala_specific.get(city_key, {})}

    # ---------------------------------------------------------------------
    # ✈ FLIGHT SEARCH (future expansion)
    # ---------------------------------------------------------------------
    def find_flights(self, origin: str, destination: str, date: str) -> Dict:
        """Placeholder: Find flights using Skyscanner API"""
        url = f"https://partners.api.skyscanner.net/apiservices/browseroutes/v1.0/IN/INR/en-IN/{origin}/{destination}/{date}?apikey={self.SKYSCANNER_API_KEY}"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                return {"success": True, "flights": data.get("Quotes", [])}
            else:
                return {"success": False, "error": res.text}
        except Exception as e:
            logger.error(f"Skyscanner flight API error: {e}")
            return {"success": False, "error": str(e)}

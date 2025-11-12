from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import os
import requests

logger = logging.getLogger(_name_)

class ItineraryAgent:
    """Generates and manages personalized travel itineraries with Granite + live weather"""

    def _init_(self, rag_pipeline, llm_handler):
        self.rag_pipeline = rag_pipeline
        self.llm_handler = llm_handler
        self.WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "c540902e3fac5160482f15da30f46ea3")

    # ----------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ----------------------------------------------------------------------
    def generate_itinerary(
        self,
        duration_days: int,
        interests: List[str],
        budget: int,
        start_date: Optional[str] = None,
        preferences: Optional[Dict] = None
    ) -> Dict:
        """Generate a custom itinerary using RAG + Granite summaries + weather info"""

        preferences = preferences or {}
        query = f"{duration_days} days {' '.join(interests)} Kerala trip"

        templates = self.rag_pipeline.search_itineraries(
            query,
            filters={'duration': duration_days, 'max_budget': budget},
            n_results=3
        )

        if templates:
            logger.info("Using itinerary template from RAG.")
            base_template = templates[0]
            itinerary = self._customize_template(base_template, interests, budget, preferences)
        else:
            logger.warning("No templates found. Generating itinerary from scratch.")
            itinerary = self._generate_from_scratch(duration_days, interests, budget, preferences)

        # Add dates and weather if provided
        if start_date:
            itinerary = self._add_dates(itinerary, start_date, preferences)

        # Calculate total cost
        itinerary['estimated_cost'] = self._calculate_itinerary_cost(itinerary)

        # Add emergency contacts and seasonal context
        itinerary['emergency_contacts'] = self._get_emergency_contacts(preferences)
        itinerary['seasonal_tip'] = self._get_seasonal_tip()

        return itinerary

    # ----------------------------------------------------------------------
    # TEMPLATE & SCRATCH GENERATION
    # ----------------------------------------------------------------------
    def _customize_template(
        self, template: Dict, interests: List[str], budget: int, preferences: Dict
    ) -> Dict:
        """Customize an itinerary template"""

        metadata = template['metadata']
        itinerary = {
            'name': f"Custom {metadata.get('theme', 'Kerala')} Journey",
            'duration_days': metadata.get('duration', 5),
            'theme': metadata.get('theme', 'mixed'),
            'daily_plan': []
        }

        for day in range(1, itinerary['duration_days'] + 1):
            daily_plan = self._generate_day_plan(
                day, interests, budget / itinerary['duration_days'], preferences
            )
            itinerary['daily_plan'].append(daily_plan)

        return itinerary

    def _generate_from_scratch(
        self, duration_days: int, interests: List[str], budget: int, preferences: Dict
    ) -> Dict:
        """Generate itinerary from scratch with attractions, hotels, and Granite summaries"""

        location = preferences.get('location', 'Munnar')
        if isinstance(location, list) and location:
            location = location[0]

        itinerary = {
            'name': f"{duration_days}-Day {location} Adventure",
            'duration_days': duration_days,
            'theme': 'custom',
            'daily_plan': []
        }

        daily_budget = budget / duration_days
        query = f"{location} {' '.join(interests[:2])}" if interests else f"{location} sightseeing attractions"

        attractions = self.rag_pipeline.search_attractions(query, n_results=duration_days * 2)
        hotel_results = self.rag_pipeline.search_hotels(
            f"{location} hotel",
            filters={'max_price': int(daily_budget * 0.5)},
            n_results=duration_days
        )

        for day in range(1, duration_days + 1):
            start_idx = (day - 1) * 2
            day_attractions = attractions[start_idx:start_idx + 2] if attractions else []
            daily_plan = {
                'day': day,
                'title': f"Day {day} - {location} Exploration",
                'activities': [],
                'accommodation': None,
                'meals': self._default_meals(daily_budget),
                'estimated_cost': 0
            }

            # Morning & afternoon activities
            for i, attr in enumerate(day_attractions[:2]):
                activity = {
                    'time': '09:00 AM' if i == 0 else '02:00 PM',
                    'name': attr['metadata'].get('name', 'Activity'),
                    'type': attr['metadata'].get('type', 'sightseeing'),
                    'duration': f"{attr['metadata'].get('duration', 2)} hours",
                    'description': self._extract_short_description(attr['document'])
                }
                daily_plan['activities'].append(activity)

            # Hotel for the night
            if hotel_results and day <= len(hotel_results):
                hotel = hotel_results[day - 1]
                daily_plan['accommodation'] = {
                    'name': hotel['metadata'].get('name', 'Hotel'),
                    'type': hotel['metadata'].get('type', 'hotel'),
                    'rating': hotel['metadata'].get('rating', 0),
                    'price': hotel['metadata'].get('price', 0),
                    'amenities': self._extract_amenities(hotel['document'])
                }
                daily_plan['estimated_cost'] += hotel['metadata'].get('price', 0)

            daily_plan['estimated_cost'] += sum(m['estimated_cost'] for m in daily_plan['meals'])

            # 🌦 Add weather and Granite summary
            daily_plan['weather'] = self._get_weather_info(location)
            daily_plan['summary'] = self._summarize_day_with_llm(daily_plan, location)

            itinerary['daily_plan'].append(daily_plan)

        return itinerary

    # ----------------------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------------------
    def _extract_short_description(self, document: str) -> str:
        sentences = document.split('.')
        for s in sentences:
            if len(s.strip()) > 20:
                return s.strip() + '.'
        return document[:150] + '...' if len(document) > 150 else document

    def _extract_amenities(self, document: str) -> List[str]:
        amenities = []
        keywords = ['pool', 'spa', 'wifi', 'breakfast', 'restaurant', 'gym', 'parking']
        doc_lower = document.lower()
        for kw in keywords:
            if kw in doc_lower:
                amenities.append(kw.title())
        return amenities[:4] if amenities else ['Standard Amenities']

    def _default_meals(self, daily_budget: float) -> List[Dict]:
        return [
            {'type': 'Breakfast', 'venue': 'Hotel', 'estimated_cost': daily_budget * 0.10},
            {'type': 'Lunch', 'venue': 'Local Restaurant', 'estimated_cost': daily_budget * 0.15},
            {'type': 'Dinner', 'venue': 'Hotel/Restaurant', 'estimated_cost': daily_budget * 0.15},
        ]

    def _generate_day_plan(
        self, day_number: int, interests: List[str], daily_budget: float, preferences: Dict
    ) -> Dict:
        plan = {
            'day': day_number,
            'title': f"Day {day_number}",
            'activities': [],
            'meals': self._default_meals(daily_budget),
            'estimated_cost': 0
        }
        query = ' '.join(interests[:2]) if interests else 'Kerala sightseeing'
        activities = self.rag_pipeline.search_attractions(query, n_results=2)
        for i, activity in enumerate(activities):
            plan['activities'].append({
                'time': ['09:00 AM', '02:00 PM'][i] if i < 2 else '10:00 AM',
                'name': activity['metadata'].get('name'),
                'type': 'attraction',
                'duration': activity['metadata'].get('duration', 2),
                'description': activity['document'][:150]
            })
        return plan

    # ----------------------------------------------------------------------
    # WEATHER, EMERGENCY, LLM SUMMARIES
    # ----------------------------------------------------------------------
    def _get_weather_info(self, city: str) -> Optional[Dict]:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.WEATHER_API_KEY}&units=metric"
            res = requests.get(url, timeout=5)
            if res.status_code != 200:
                return None
            data = res.json()
            return {
                'temp': data['main']['temp'],
                'condition': data['weather'][0]['description'].capitalize(),
                'humidity': data['main']['humidity']
            }
        except Exception as e:
            logger.warning(f"Weather fetch failed for {city}: {e}")
            return None

    def _get_emergency_contacts(self, preferences: Dict) -> Dict:
        base = {"police": "100", "ambulance": "108", "fire": "101", "tourist helpline": "1363"}
        city = str(preferences.get('location', 'kerala')).lower()
        city_contacts = {
            'kochi': {"nearest hospital": "Ernakulam Medical Centre – 0484 290 7000"},
            'thiruvananthapuram': {"nearest hospital": "KIMS Health – 0471 294 1000"},
            'munnar': {"nearest hospital": "Tata General Hospital – 04865 230 444"},
            'wayanad': {"nearest hospital": "Assumption Hospital – 04936 260 421"},
            'alleppey': {"nearest hospital": "SD Hospital – 0477 223 0250"}
        }
        return {**base, **city_contacts.get(city, {})}

    def _summarize_day_with_llm(self, day_plan: Dict, location: str) -> str:
        """Use Granite (LLM) to create natural language summary"""
        try:
            activities = ', '.join([a['name'] for a in day_plan['activities']]) or 'local attractions'
            weather = day_plan.get('weather', {}).get('condition', 'pleasant weather')
            prompt = f"""
            Write a 2-3 sentence summary for a travel itinerary day in {location}.
            Activities: {activities}.
            Weather: {weather}.
            Tone: friendly, concise, travel-guide style.
            """
            return self.llm_handler.generate(prompt, max_tokens=80)
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return "Enjoy exploring local attractions and immersing in Kerala’s beauty!"

    def _get_seasonal_tip(self) -> str:
        month = datetime.now().month
        if month in [6, 7, 8]:
            return "🌧 Monsoon season — expect lush greenery and rain showers!"
        elif month in [12, 1, 2]:
            return "🌤 Winter in Kerala — perfect for beaches and backwaters!"
        else:
            return "☀ Warm tropical weather — great for sightseeing and outdoor activities!"

    # ----------------------------------------------------------------------
    # COST + EXPORT
    # ----------------------------------------------------------------------
    def _add_dates(self, itinerary: Dict, start_date: str, preferences: Dict) -> Dict:
        start = datetime.fromisoformat(start_date)
        for i, day in enumerate(itinerary['daily_plan']):
            day_date = start + timedelta(days=i)
            day['date'] = day_date.strftime('%Y-%m-%d')
            day['day_of_week'] = day_date.strftime('%A')
            city = preferences.get('location', 'Kerala')
            day['weather'] = self._get_weather_info(city)
        return itinerary

    def _calculate_itinerary_cost(self, itinerary: Dict) -> Dict:
        total = 0
        breakdown = {'accommodation': 0, 'activities': 0, 'meals': 0, 'transport': 0}
        for day in itinerary.get('daily_plan', []):
            if day.get('accommodation'):
                acc_cost = day['accommodation'].get('price', 0)
                breakdown['accommodation'] += acc_cost
                total += acc_cost
            for meal in day.get('meals', []):
                meal_cost = meal.get('estimated_cost', 0)
                breakdown['meals'] += meal_cost
                total += meal_cost
        breakdown['transport'] = total * 0.1
        total += breakdown['transport']
        return {'total': total, 'breakdown': breakdown, 'currency': 'INR'}

    def export_itinerary(self, itinerary: Dict, format: str = 'json') -> str:
        if format == 'json':
            import json
            return json.dumps(itinerary, indent=2)
        elif format == 'text':
            output = f"# {itinerary['name']}\nDuration: {itinerary['duration_days']} days\n\n"
            for day in itinerary['daily_plan']:
                output += f"## Day {day['day']} - {day['title']} ({day.get('date', '')})\n"
                if 'weather' in day:
                    output += f"🌦 {day['weather']['condition']} - {day['weather']['temp']}°C\n"
                for a in day.get('activities', []):
                    output += f"- {a['time']}: {a['name']}\n"
                if day.get('summary'):
                    output += f"\n💬 {day['summary']}\n"
                if day.get('accommodation'):
                    output += f"🏨 Stay: {day['accommodation']['name']}\n"
                output += "\n"
            if 'estimated_cost' in itinerary:
                output += f"💰 Total Cost: ₹{itinerary['estimated_cost']['total']:,.0f}\n"
            if 'seasonal_tip' in itinerary:
                output += f"\n{itinerary['seasonal_tip']}\n"
            output += "\n🚨 Emergency Contacts:\n"
            for k, v in itinerary.get('emergency_contacts', {}).items():
                output += f"- {k.title()}: {v}\n"
            return output
        return str(itinerary)

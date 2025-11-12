"""Knowledge base service for Kerala travel information"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(_name_)

class KnowledgeBase:
    """Static knowledge base for Kerala travel information"""
    
    def _init_(self):
        self.kerala_info = self._load_kerala_info()
        self.travel_tips = self._load_travel_tips()
        self.faq = self._load_faq()
    
    def _load_kerala_info(self) -> Dict:
        """Load general Kerala information"""
        return {
            'overview': {
                'name': 'Kerala',
                'nickname': "God's Own Country",
                'capital': 'Thiruvananthapuram',
                'language': 'Malayalam',
                'best_time': 'October to March',
                'currency': 'Indian Rupee (INR)',
                'area': '38,852 km²',
                'population': '~35 million',
                'climate': 'Tropical monsoon'
            },
            'regions': {
                'north': {
                    'districts': ['Kasaragod', 'Kannur', 'Wayanad', 'Kozhikode'],
                    'highlights': ['Beaches', 'Hill stations', 'Spice plantations', 'Theyyam']
                },
                'central': {
                    'districts': ['Malappuram', 'Palakkad', 'Thrissur', 'Ernakulam', 'Idukki', 'Kottayam'],
                    'highlights': ['Backwaters', 'Hill stations', 'Tea estates', 'Waterfalls', 'Cultural centers']
                },
                'south': {
                    'districts': ['Alappuzha', 'Pathanamthitta', 'Kollam', 'Thiruvananthapuram'],
                    'highlights': ['Backwaters', 'Beaches', 'Temples', 'Ayurveda centers']
                }
            },
            'weather': {
                'summer': {'months': 'March-May', 'temp': '28-35°C', 'description': 'Hot and humid'},
                'monsoon': {'months': 'June-September', 'temp': '24-30°C', 'description': 'Heavy rainfall'},
                'winter': {'months': 'October-February', 'temp': '20-28°C', 'description': 'Pleasant and dry'}
            }
        }
    
    def _load_travel_tips(self) -> Dict:
        """Load travel tips and recommendations"""
        return {
            'packing': [
                'Light cotton clothes for summer',
                'Umbrella and raincoat during monsoon',
                'Light jacket for hill stations',
                'Comfortable walking shoes',
                'Sunscreen and mosquito repellent'
            ],
            'health': [
                'Drink bottled water',
                'Carry basic medicines',
                'Get travel insurance',
                'Be careful with street food initially',
                'Stay hydrated in hot weather'
            ],
            'safety': [
                'Keep valuables secure',
                'Use registered taxis or ride-sharing apps',
                'Be cautious of touts at tourist spots',
                'Respect local customs and dress modestly',
                'Keep emergency contacts handy'
            ],
            'etiquette': [
                'Remove shoes before entering temples',
                'Dress modestly at religious places',
                'Ask permission before photographing people',
                'Bargain politely at markets',
                'Learn basic Malayalam phrases'
            ],
            'transportation': [
                'Kerala SRTC buses are economical',
                'Auto-rickshaws use meters in cities',
                'Houseboats must be booked in advance',
                'Trains connect major cities',
                'Taxis available via apps like Ola, Uber'
            ],
            'budget_saving': [
                'Travel during off-season',
                'Stay in homestays instead of hotels',
                'Eat at local restaurants',
                'Use public transport',
                'Book activities in advance',
                'Look for package deals'
            ]
        }
    
    def _load_faq(self) -> List[Dict]:
        """Load frequently asked questions"""
        return [
            {
                'question': 'What is the best time to visit Kerala?',
                'answer': 'October to March is the best time with pleasant weather. Monsoon (June-September) is great for Ayurveda but brings heavy rain.'
            },
            {
                'question': 'How many days do I need for Kerala?',
                'answer': '5-7 days is ideal for covering major highlights. 3-4 days for a short trip, 10-14 days for comprehensive exploration.'
            },
            {
                'question': 'Is Kerala expensive?',
                'answer': 'Kerala can suit any budget. Budget travelers: ₹2000-3000/day, Mid-range: ₹5000-10000/day, Luxury: ₹15000+/day'
            },
            {
                'question': 'Do I need a visa?',
                'answer': 'Foreign nationals need an Indian visa. Domestic travelers need no special permits.'
            },
            {
                'question': 'Is Kerala safe for solo travelers?',
                'answer': 'Yes, Kerala is generally safe. Follow standard precautions and respect local customs.'
            },
            {
                'question': 'What should I try in Kerala?',
                'answer': 'Must-try: Kerala Sadya, fish curry, appam, puttu, banana chips. Don\'t miss Kerala-style seafood!'
            },
            {
                'question': 'Are houseboats worth it?',
                'answer': 'Absolutely! Houseboat stays in Alleppey backwaters are quintessential Kerala experiences.'
            },
            {
                'question': 'What to buy in Kerala?',
                'answer': 'Popular items: spices, tea, coffee, coir products, kathakali masks, aranmula mirrors, handloom fabrics'
            }
        ]
    
    def get_info(self, category: str) -> Optional[Dict]:
        """Get information by category"""
        categories = {
            'overview': self.kerala_info['overview'],
            'regions': self.kerala_info['regions'],
            'weather': self.kerala_info['weather'],
            'travel_tips': self.travel_tips,
            'faq': self.faq
        }
        return categories.get(category)
    
    def search_faq(self, query: str) -> List[Dict]:
        """Search FAQ by query"""
        query_lower = query.lower()
        results = []
        
        for faq in self.faq:
            if (query_lower in faq['question'].lower() or 
                query_lower in faq['answer'].lower()):
                results.append(faq)
        
        return results
    
    def get_destination_info(self, destination: str) -> Dict:
        """Get information about a specific destination"""
        
        destinations = {
            'kochi': {
                'name': 'Kochi (Cochin)',
                'type': 'City',
                'highlights': ['Fort Kochi', 'Chinese Fishing Nets', 'Mattancherry Palace', 'Jewish Synagogue'],
                'best_for': ['History', 'Culture', 'Shopping'],
                'duration': '2-3 days',
                'access': 'Major airport and railway station'
            },
            'munnar': {
                'name': 'Munnar',
                'type': 'Hill Station',
                'highlights': ['Tea plantations', 'Eravikulam National Park', 'Mattupetty Dam'],
                'best_for': ['Nature', 'Trekking', 'Photography'],
                'duration': '2-3 days',
                'access': '4-5 hours from Kochi by road'
            },
            'alleppey': {
                'name': 'Alleppey (Alappuzha)',
                'type': 'Backwaters',
                'highlights': ['Houseboat cruises', 'Backwater villages', 'Nehru Trophy Snake Boat Race'],
                'best_for': ['Relaxation', 'Houseboats', 'Backwaters'],
                'duration': '1-2 days',
                'access': '1.5 hours from Kochi by road'
            },
            'thekkady': {
                'name': 'Thekkady',
                'type': 'Wildlife Sanctuary',
                'highlights': ['Periyar Wildlife Sanctuary', 'Spice plantations', 'Bamboo rafting'],
                'best_for': ['Wildlife', 'Nature', 'Adventure'],
                'duration': '1-2 days',
                'access': '4 hours from Kochi by road'
            },
            'kovalam': {
                'name': 'Kovalam',
                'type': 'Beach Resort',
                'highlights': ['Lighthouse Beach', 'Water sports', 'Ayurvedic spas'],
                'best_for': ['Beach', 'Relaxation', 'Ayurveda'],
                'duration': '2-3 days',
                'access': '20 km from Thiruvananthapuram'
            },
            'wayanad': {
                'name': 'Wayanad',
                'type': 'Hill Station',
                'highlights': ['Chembra Peak', 'Edakkal Caves', 'Wildlife sanctuaries'],
                'best_for': ['Trekking', 'Wildlife', 'Nature'],
                'duration': '2-3 days',
                'access': '3 hours from Kozhikode by road'
            }
        }
        
        dest_key = destination.lower().strip()
        return destinations.get(dest_key, {})
    
    def get_activity_info(self, activity: str) -> Dict:
        """Get information about specific activities"""
        
        activities = {
            'houseboat': {
                'name': 'Houseboat Cruise',
                'description': 'Traditional Kettuvallam boats converted into floating hotels',
                'duration': '1 day / 1 night typical',
                'cost': '₹8000-₹25000 per night',
                'best_places': ['Alleppey', 'Kumarakom'],
                'tips': ['Book in advance', 'Check meal inclusions', 'Choose sunset cruise']
            },
            'ayurveda': {
                'name': 'Ayurveda Treatment',
                'description': 'Traditional Indian medicine and wellness treatments',
                'duration': '3-21 days for full packages',
                'cost': '₹3000-₹15000 per day',
                'best_places': ['Kovalam', 'Varkala', 'Kochi'],
                'tips': ['Consult doctor first', 'Choose certified centers', 'Monsoon is best season']
            },
            'trekking': {
                'name': 'Trekking',
                'description': 'Mountain treks through tea estates and forests',
                'duration': 'Half day to full day',
                'cost': '₹500-₹2000 with guide',
                'best_places': ['Munnar', 'Wayanad', 'Vagamon'],
                'tips': ['Hire local guide', 'Start early', 'Carry water and snacks']
            },
            'wildlife': {
                'name': 'Wildlife Safari',
                'description': 'Boat and jeep safaris in wildlife sanctuaries',
                'duration': '2-3 hours',
                'cost': '₹300-₹2000 per person',
                'best_places': ['Periyar', 'Wayanad', 'Silent Valley'],
                'tips': ['Book early morning slots', 'Wear neutral colors', 'Be quiet']
            }
        }
        
        activity_key = activity.lower().strip()
        return activities.get(activity_key, {})
    
    def get_seasonal_recommendations(self, month: int) -> Dict:
        """Get recommendations based on month"""
        
        if month in [3, 4, 5]:  # Summer
            return {
                'season': 'Summer',
                'weather': 'Hot and humid',
                'recommended_places': ['Munnar', 'Wayanad', 'Vagamon'],
                'activities': ['Hill station visits', 'Tea estate tours'],
                'avoid': ['Beaches during midday'],
                'tips': ['Stay hydrated', 'Use sunscreen', 'Visit early morning/evening']
            }
        elif month in [6, 7, 8, 9]:  # Monsoon
            return {
                'season': 'Monsoon',
                'weather': 'Heavy rainfall',
                'recommended_places': ['Ayurveda centers', 'Hill stations'],
                'activities': ['Ayurveda treatments', 'Waterfall visits'],
                'avoid': ['Beach activities', 'Long road trips'],
                'tips': ['Carry rain gear', 'Book indoor activities', 'Enjoy fresh greenery']
            }
        else:  # Winter (Oct-Feb)
            return {
                'season': 'Winter',
                'weather': 'Pleasant and dry',
                'recommended_places': ['Beaches', 'Backwaters', 'All destinations'],
                'activities': ['Houseboats', 'Beach activities', 'Wildlife safaris'],
                'avoid': 'Nothing - best time!',
                'tips': ['Book in advance', 'Expect higher prices', 'Enjoy festivals']
            }

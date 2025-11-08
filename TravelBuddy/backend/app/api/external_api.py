"""External API integrations"""

import httpx
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(_name_)

class WeatherAPI:
    """Weather API integration"""
    
    def _init_(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_weather(self, city: str) -> Optional[Dict]:
        """Get current weather for a city"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params={
                        "q": f"{city},IN",
                        "appid": self.api_key,
                        "units": "metric"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "city": city,
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "description": data["weather"][0]["description"],
                        "wind_speed": data["wind"]["speed"]
                    }
                
                logger.error(f"Weather API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Weather API exception: {e}")
            return None
    
    async def get_forecast(self, city: str, days: int = 5) -> Optional[Dict]:
        """Get weather forecast"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params={
                        "q": f"{city},IN",
                        "appid": self.api_key,
                        "units": "metric",
                        "cnt": days * 8  # 8 forecasts per day (3-hour intervals)
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Process forecast data
                    forecasts = []
                    for item in data["list"][:days]:
                        forecasts.append({
                            "date": item["dt_txt"],
                            "temp": item["main"]["temp"],
                            "description": item["weather"][0]["description"]
                        })
                    
                    return {
                        "city": city,
                        "forecasts": forecasts
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Forecast API exception: {e}")
            return None


class FlightAPI:
    """Flight search API integration (placeholder)"""
    
    def _init_(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.skyscanner.net/v3"
    
    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None
    ) -> Optional[Dict]:
        """Search for flights"""
        
        # This is a placeholder implementation
        # In production, integrate with actual flight API
        
        try:
            logger.info(f"Searching flights: {origin} -> {destination}")
            
            # Mock response
            return {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "flights": [
                    {
                        "airline": "Air India",
                        "price": 5500,
                        "duration": "2h 30m",
                        "departure": "10:00 AM",
                        "arrival": "12:30 PM"
                    },
                    {
                        "airline": "IndiGo",
                        "price": 4800,
                        "duration": "2h 15m",
                        "departure": "2:00 PM",
                        "arrival": "4:15 PM"
                    }
                ],
                "note": "This is sample data. Integrate with real API for actual flights."
            }
            
        except Exception as e:
            logger.error(f"Flight API exception: {e}")
            return None


class CurrencyAPI:
    """Currency conversion API"""
    
    def _init_(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
    
    async def convert(
        self,
        amount: float,
        from_currency: str = "USD",
        to_currency: str = "INR"
    ) -> Optional[Dict]:
        """Convert currency"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/{from_currency}")
                
                if response.status_code == 200:
                    data = response.json()
                    rate = data["rates"].get(to_currency)
                    
                    if rate:
                        converted = amount * rate
                        return {
                            "from": from_currency,
                            "to": to_currency,
                            "amount": amount,
                            "converted": round(converted, 2),
                            "rate": rate
                        }
                
                return None
                
        except Exception as e:
            logger.error(f"Currency API exception: {e}")
            return None


# Export instances
def get_weather_api(api_key: str) -> WeatherAPI:
    """Get Weather API instance"""
    return WeatherAPI(api_key)

def get_flight_api(api_key: str) -> FlightAPI:
    """Get Flight API instance"""
    return FlightAPI(api_key)

def get_currency_api() -> CurrencyAPI:
    """Get Currency API instance"""
    return CurrencyAPI()

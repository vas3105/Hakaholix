# data_collection/collect_attractions.py
import requests
import json
import time
import os


def collect_kerala_attractions():
    """
    Collect Kerala attractions using OpenStreetMap Nominatim API (Free tier, no key needed)
    """

    kerala_cities = [
        "Kochi", "Munnar", "Alleppey", "Kumarakom",
        "Thekkady", "Wayanad", "Kovalam", "Varkala"
    ]

    attractions = []

    for city in kerala_cities:
        print(f"Collecting attractions for {city}...")

        # Use OpenStreetMap Nominatim (free, no key)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"tourist attractions {city} Kerala India",
            "format": "json",
            "limit": 10
        }

        response = requests.get(url, params=params, headers={'User-Agent': 'KeralaTravelAI/1.0'})
        if response.status_code != 200:
            print(f"⚠ Failed to fetch data for {city}")
            continue

        places = response.json()

        for place in places:
            attraction = {
                "id": f"attr_{len(attractions):03d}",
                "name": place['display_name'].split(',')[0],
                "location": {
                    "city": city,
                    "coordinates": {
                        "lat": float(place['lat']),
                        "lng": float(place['lon'])
                    }
                },
                "details": {
                    "type": classify_attraction_type(place['display_name']),
                    "duration_hours": estimate_duration(place['display_name'])
                }
            }
            attractions.append(attraction)

        time.sleep(1)  # Rate limiting

    # Enrich with manual data
    attractions = enrich_with_manual_data(attractions)

    # Ensure output directory exists
    os.makedirs('processed_data', exist_ok=True)

    # Save the final JSON
    with open('processed_data/kerala_attractions.json', 'w', encoding='utf-8') as f:
        json.dump({"attractions": attractions}, f, indent=2, ensure_ascii=False)

    print("✅ Kerala attractions data collected successfully!")
    return attractions


def classify_attraction_type(name):
    """Classify attraction by name"""
    name_lower = name.lower()

    if any(word in name_lower for word in ['temple', 'church', 'mosque', 'synagogue']):
        return 'religious'
    elif any(word in name_lower for word in ['beach', 'lake', 'waterfall', 'hill']):
        return 'nature_scenic'
    elif any(word in name_lower for word in ['museum', 'gallery', 'palace', 'fort']):
        return 'cultural_historical'
    elif any(word in name_lower for word in ['park', 'sanctuary', 'reserve']):
        return 'wildlife_nature'
    else:
        return 'general'


def estimate_duration(name):
    """Estimate typical visit duration"""
    name_lower = name.lower()

    if any(word in name_lower for word in ['museum', 'gallery', 'sanctuary']):
        return 2
    elif any(word in name_lower for word in ['temple', 'church']):
        return 1
    elif any(word in name_lower for word in ['beach', 'hill', 'trek']):
        return 3
    else:
        return 2


def enrich_with_manual_data(attractions):
    """Add manually curated Kerala highlights"""
    kerala_highlights = [
        {
            "id": "attr_munnar_tea",
            "name": "Munnar Tea Gardens",
            "location": {"city": "Munnar", "coordinates": {"lat": 10.0889, "lng": 77.0595}},
            "details": {
                "type": "nature_scenic",
                "duration_hours": 3,
                "entry_fee_inr": 50,
                "best_time_of_day": "morning"
            },
            "insider_tips": ["Visit during sunrise", "Book factory tour in advance"],
            "best_months": ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_backwater_cruise",
            "name": "Alleppey Backwater Houseboat",
            "location": {"city": "Alleppey", "coordinates": {"lat": 9.4981, "lng": 76.3388}},
            "details": {
                "type": "unique_experience",
                "duration_hours": 8,
                "price_range_inr": [8000, 25000],
                "best_time_of_day": "all_day"
            },
            "insider_tips": ["Book AC houseboats in summer", "Sunset cruises are most romantic"],
            "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
        },
        {
            "id": "attr_athirapally_falls",
            "name": "Athirappilly Waterfalls",
            "location": {"city": "Thrissur", "coordinates": {"lat": 10.2849, "lng": 76.5680}},
            "details": {"type": "nature_scenic", "duration_hours": 2, "entry_fee_inr": 50},
            "insider_tips": ["Best visited after monsoon", "Carry rain gear"],
            "best_months": ["Jul", "Aug", "Sep", "Oct"]
        },
        {
            "id": "attr_periyar_wildlife",
            "name": "Periyar Wildlife Sanctuary",
            "location": {"city": "Thekkady", "coordinates": {"lat": 9.4669, "lng": 77.2360}},
            "details": {"type": "wildlife_nature", "duration_hours": 4, "entry_fee_inr": 150},
            "insider_tips": ["Take early morning boat safari", "Wear dull-coloured clothes"],
            "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_kovalam_beach",
            "name": "Kovalam Beach",
            "location": {"city": "Kovalam", "coordinates": {"lat": 8.3989, "lng": 76.9784}},
            "details": {"type": "nature_scenic", "duration_hours": 3},
            "insider_tips": ["Perfect for sunset photography", "Try beachside seafood stalls"],
            "best_months": ["Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_varkala_cliff",
            "name": "Varkala Cliff Beach",
            "location": {"city": "Varkala", "coordinates": {"lat": 8.7334, "lng": 76.7169}},
            "details": {"type": "nature_scenic", "duration_hours": 3},
            "insider_tips": ["Walk along the cliff trail", "Avoid swimming during monsoon"],
            "best_months": ["Nov", "Dec", "Jan", "Feb", "Mar"]
        },
        {
            "id": "attr_fort_kochi",
            "name": "Fort Kochi & Chinese Fishing Nets",
            "location": {"city": "Kochi", "coordinates": {"lat": 9.9653, "lng": 76.2421}},
            "details": {"type": "cultural_historical", "duration_hours": 2},
            "insider_tips": ["Best visited around sunset", "Explore nearby cafes"],
            "best_months": ["Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_mattancherry_palace",
            "name": "Mattancherry Palace",
            "location": {"city": "Kochi", "coordinates": {"lat": 9.9620, "lng": 76.2414}},
            "details": {"type": "cultural_historical", "duration_hours": 1, "entry_fee_inr": 20},
            "insider_tips": ["Closed on Fridays", "Photography not allowed inside"],
            "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_kumarakom_bird_sanctuary",
            "name": "Kumarakom Bird Sanctuary",
            "location": {"city": "Kumarakom", "coordinates": {"lat": 9.6170, "lng": 76.4300}},
            "details": {"type": "wildlife_nature", "duration_hours": 3, "entry_fee_inr": 50},
            "insider_tips": ["Early mornings best for birdwatching", "Carry binoculars"],
            "best_months": ["Nov", "Dec", "Jan", "Feb", "Mar"]
        },
        {
            "id": "attr_wayanad_eden",
            "name": "Wayanad Edakkal Caves",
            "location": {"city": "Wayanad", "coordinates": {"lat": 11.6086, "lng": 76.2366}},
            "details": {"type": "cultural_historical", "duration_hours": 2, "entry_fee_inr": 30},
            "insider_tips": ["Climb involves 30 mins hike", "Carry water bottles"],
            "best_months": ["Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_pookode_lake",
            "name": "Pookode Lake",
            "location": {"city": "Wayanad", "coordinates": {"lat": 11.5485, "lng": 76.0120}},
            "details": {"type": "nature_scenic", "duration_hours": 2, "entry_fee_inr": 30},
            "insider_tips": ["Boating available", "Great for families"],
            "best_months": ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_vembanad_lake",
            "name": "Vembanad Lake",
            "location": {"city": "Kumarakom", "coordinates": {"lat": 9.6270, "lng": 76.4250}},
            "details": {"type": "nature_scenic", "duration_hours": 3},
            "insider_tips": ["Ideal for sunset cruises", "Try local toddy shops nearby"],
            "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_bekal_fort",
            "name": "Bekal Fort",
            "location": {"city": "Kasaragod", "coordinates": {"lat": 12.3876, "lng": 75.0346}},
            "details": {"type": "cultural_historical", "duration_hours": 2, "entry_fee_inr": 25},
            "insider_tips": ["Sunset views from fort walls", "Carry hat or umbrella"],
            "best_months": ["Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_marari_beach",
            "name": "Marari Beach",
            "location": {"city": "Alleppey", "coordinates": {"lat": 9.6124, "lng": 76.3111}},
            "details": {"type": "nature_scenic", "duration_hours": 3},
            "insider_tips": ["Less crowded than Kovalam", "Great for sunrise photography"],
            "best_months": ["Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_vagamon_meadows",
            "name": "Vagamon Meadows",
            "location": {"city": "Vagamon", "coordinates": {"lat": 9.6836, "lng": 76.9050}},
            "details": {"type": "nature_scenic", "duration_hours": 3},
            "insider_tips": ["Ideal for paragliding", "Cool climate year-round"],
            "best_months": ["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_nelliampathy_hills",
            "name": "Nelliampathy Hills",
            "location": {"city": "Palakkad", "coordinates": {"lat": 10.5337, "lng": 76.6870}},
            "details": {"type": "nature_scenic", "duration_hours": 4},
            "insider_tips": ["Scenic drive through tea estates", "Avoid heavy monsoon months"],
            "best_months": ["Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_silent_valley",
            "name": "Silent Valley National Park",
            "location": {"city": "Palakkad", "coordinates": {"lat": 11.0640, "lng": 76.4428}},
            "details": {"type": "wildlife_nature", "duration_hours": 5, "entry_fee_inr": 100},
            "insider_tips": ["Need forest department permission", "Carry food and water"],
            "best_months": ["Dec", "Jan", "Feb", "Mar"]
        },
        {
            "id": "attr_ponmudi_hill_station",
            "name": "Ponmudi Hill Station",
            "location": {"city": "Thiruvananthapuram", "coordinates": {"lat": 8.7598, "lng": 77.1169}},
            "details": {"type": "nature_scenic", "duration_hours": 4},
            "insider_tips": ["Wear warm clothes", "Visit early for fog views"],
            "best_months": ["Oct", "Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_peechi_dam",
            "name": "Peechi Dam",
            "location": {"city": "Thrissur", "coordinates": {"lat": 10.5287, "lng": 76.3488}},
            "details": {"type": "nature_scenic", "duration_hours": 2},
            "insider_tips": ["Good picnic spot", "Avoid weekends for less crowd"],
            "best_months": ["Nov", "Dec", "Jan", "Feb"]
        },
        {
            "id": "attr_thusharagiri_waterfalls",
            "name": "Thusharagiri Waterfalls",
            "location": {"city": "Kozhikode", "coordinates": {"lat": 11.4707, "lng": 75.9324}},
            "details": {"type": "nature_scenic", "duration_hours": 3},
            "insider_tips": ["Good for trekking", "Best after monsoon"],
            "best_months": ["Jul", "Aug", "Sep", "Oct"]
        }
    ]

    return attractions + kerala_highlights


if _name_ == "_main_":
    collect_kerala_attractions()

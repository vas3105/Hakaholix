# data_sources.py
DATA_SOURCES = {
    "hotels": [
        "kaggle: kerala-dataset-from-bookingcom",
        "kaggle: google-indian-hotel-data", 
        "manual_scraping: booking.com Kerala hotels"
    ],
    "attractions": [
        "manual_scraping: Kerala Tourism Official",
        "google_places_api: Free tier (Basic Details)",
        "tripadvisor: Top Kerala attractions"
    ],
    "restaurants": [
        "google_places_api: Kerala restaurants",
        "zomato_api: Free tier",
        "manual_curation: 50 top Kerala eateries"
    ],
    "experiences": [
        "kerala_tourism: Official packages",
        "manual_curation: Houseboats, ayurveda, backwaters"
    ],
    "influencer_content": [
        "youtube_api: Search 'Kerala travel vlog'",
        "manual_curation: Top 10 Kerala travel creators"
    ],
    "weather": [
        "open_meteo_api: Free, no key required",
        "weatherstack: Free tier (1000 calls/month)"
    ],
    "user_reviews": [
        "kaggle: hotel-reviews dataset",
        "google_reviews: Via Places API"
    ]
}

# data_collection/curate_influencers.py
import json
import os

def curate_kerala_influencers():
    """
    Curate Kerala travel influencers and their YouTube video details manually.
    This dataset is useful for recommendation, sentiment, or content analysis.
    """

    influencers = [
        {
            "id": "inf_mark_wiens",
            "name": "Mark Wiens",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@MarkWiens",
            "kerala_videos": [
                {
                    "title": "Ultimate Kerala Food Tour!!",
                    "video_id": "6sKxCO9mTBs",
                    "video_url": "https://www.youtube.com/watch?v=6sKxCO9mTBs"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["food", "culture"]
            }
        },
        {
            "id": "inf_ebbin_jose",
            "name": "Ebbin Jose",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@FoodNTravelbyEbbinJose",
            "kerala_videos": [
                {
                    "title": "Kerala Toddy Shop Food Experience",
                    "video_id": "B4xU6UmLWxI",
                    "video_url": "https://www.youtube.com/watch?v=B4xU6UmLWxI"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["street_food", "local_culture"]
            }
        },
        {
            "id": "inf_tanya_khanijow",
            "name": "Tanya Khanijow",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@TanyaKhanijow",
            "kerala_videos": [
                {
                    "title": "Kerala Solo Travel Vlog | Alleppey Backwaters",
                    "video_id": "ZxjK5hvX8yM",
                    "video_url": "https://www.youtube.com/watch?v=ZxjK5hvX8yM"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["solo_female", "adventure"]
            }
        },
        {
            "id": "inf_visa2explore",
            "name": "Visa2Explore",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@Visa2explore",
            "kerala_videos": [
                {
                    "title": "Exploring Kerala Food | Kochi to Alleppey Journey",
                    "video_id": "aeUIsxkKiEo",
                    "video_url": "https://www.youtube.com/watch?v=aeUIsxkKiEo"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["food", "culture", "travel_tips"]
            }
        },
        {
            "id": "inf_nomadic_indian",
            "name": "Nomadic Indian",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@NomadicIndian",
            "kerala_videos": [
                {
                    "title": "Exploring Wayanad - Kerala Vlog",
                    "video_id": "gCk7iFtqXzA",
                    "video_url": "https://www.youtube.com/watch?v=gCk7iFtqXzA"
                }
            ],
            "travel_style": {
                "budget": "low",
                "focus": ["solo_travel", "budget_tips"]
            }
        },
        {
            "id": "inf_malvika_sitlani",
            "name": "Malvika Sitlani",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@MalvikaSitlani",
            "kerala_videos": [
                {
                    "title": "Luxury Stay in Munnar | Kerala Travel Vlog",
                    "video_id": "bOZMLjq8dpE",
                    "video_url": "https://www.youtube.com/watch?v=bOZMLjq8dpE"
                }
            ],
            "travel_style": {
                "budget": "luxury",
                "focus": ["travel", "luxury_stay"]
            }
        },
        {
            "id": "inf_karl_rock",
            "name": "Karl Rock",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@KarlRock",
            "kerala_videos": [
                {
                    "title": "Why I Love Kerala | South India Travel",
                    "video_id": "aZrGZEKtIbM",
                    "video_url": "https://www.youtube.com/watch?v=aZrGZEKtIbM"
                }
            ],
            "travel_style": {
                "budget": "budget",
                "focus": ["culture", "street_life"]
            }
        },
        {
            "id": "inf_tourwithshikha",
            "name": "Tour With Shikha",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@tourwithshikha",
            "kerala_videos": [
                {
                    "title": "Kerala Houseboat Experience | Alleppey Vlog",
                    "video_id": "G7RShpDNZho",
                    "video_url": "https://www.youtube.com/watch?v=G7RShpDNZho"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["family_travel", "village_experience"]
            }
        },
        {
            "id": "inf_kerala_foodie",
            "name": "Kerala Foodie",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@keralafoodie",
            "kerala_videos": [
                {
                    "title": "Best Food in Kochi - Kayees Rahmathulla Biryani",
                    "video_id": "y_biK3uA9nM",
                    "video_url": "https://www.youtube.com/watch?v=y_biK3uA9nM"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["food", "local_dining"]
            }
        },
        {
            "id": "inf_food_n_travel_vlog",
            "name": "Food N Travel Vlog",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@foodntravelvlog",
            "kerala_videos": [
                {
                    "title": "Paragon Restaurant Kozhikode | Kerala Food Review",
                    "video_id": "S8XKeVxczmA",
                    "video_url": "https://www.youtube.com/watch?v=S8XKeVxczmA"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["food", "restaurants"]
            }
        },
        {
            "id": "inf_malayali_traveller",
            "name": "Malayali Traveller",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@malayalitraveller",
            "kerala_videos": [
                {
                    "title": "Hidden Waterfalls of Wayanad",
                    "video_id": "C5SVNxoG0vE",
                    "video_url": "https://www.youtube.com/watch?v=C5SVNxoG0vE"
                }
            ],
            "travel_style": {
                "budget": "low",
                "focus": ["nature", "adventure"]
            }
        },
        {
            "id": "inf_sajeesh_vlogs",
            "name": "Sajeesh Vlogs",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@sajeeshvlogs",
            "kerala_videos": [
                {
                    "title": "Street Food in Trivandrum",
                    "video_id": "5e7EFn8ZcAg",
                    "video_url": "https://www.youtube.com/watch?v=5e7EFn8ZcAg"
                }
            ],
            "travel_style": {
                "budget": "low",
                "focus": ["street_food", "local_life"]
            }
        },
        {
            "id": "inf_sanketh_vlogs",
            "name": "Sanketh Vlogs",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@sankethvlogs",
            "kerala_videos": [
                {
                    "title": "Kerala’s Top 5 Coastal Foods",
                    "video_id": "pY6Qm0q8x8s",
                    "video_url": "https://www.youtube.com/watch?v=pY6Qm0q8x8s"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["food", "coastal_cuisine"]
            }
        },
        {
            "id": "inf_keralagram",
            "name": "Keralagram",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@keralagram",
            "kerala_videos": [
                {
                    "title": "Munnar Travel Guide 2024 | Top Things to Do",
                    "video_id": "tcbzGlzTjVQ",
                    "video_url": "https://www.youtube.com/watch?v=tcbzGlzTjVQ"
                }
            ],
            "travel_style": {
                "budget": "mid_range",
                "focus": ["travel_guide", "nature"]
            }
        },
        {
            "id": "inf_kerala_backpackers",
            "name": "Kerala Backpackers",
            "platform": "YouTube",
            "channel_url": "https://www.youtube.com/@keralabackpackers",
            "kerala_videos": [
                {
                    "title": "Varkala Cliff | Kerala Budget Travel",
                    "video_id": "jh9aPlk93Jo",
                    "video_url": "https://www.youtube.com/watch?v=jh9aPlk93Jo"
                }
            ],
            "travel_style": {
                "budget": "low",
                "focus": ["backpacking", "budget_travel"]
            }
        }
    ]

    os.makedirs('processed_data', exist_ok=True)

    with open('processed_data/kerala_influencers.json', 'w', encoding='utf-8') as f:
        json.dump({"influencers": influencers}, f, indent=2, ensure_ascii=False)

    print("✅ Kerala influencer data saved to processed_data/kerala_influencers.json")
    return influencers


if _name_ == "_main_":
    curate_kerala_influencers()

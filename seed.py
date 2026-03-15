import requests
from config.db import properties_collection, images_collection
from dotenv import load_dotenv
import os
import random

load_dotenv()

UNSPLASH_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def fetch_images(query, count=4):
    url = f"https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": count,
        "orientation": "landscape",
        "client_id": UNSPLASH_KEY
    }
    res = requests.get(url, params=params)
    data = res.json()
    return [photo["urls"]["regular"] for photo in data.get("results", [])]

demo_properties = [
    {
        "title": "Luxury 3BHK Apartment in Anna Nagar",
        "location": "Anna Nagar, Chennai",
        "price": 8500000,
        "land_size": "1850 sq ft",
        "description": "Spacious modern apartment with premium finishes, modular kitchen and stunning city views. Gated community with 24/7 security.",
        "style": "modern",
        "rooms": ["modern living room interior", "modern bedroom interior", "modern kitchen interior", "modern bathroom interior"]
    },
    {
        "title": "Independent Villa with Pool",
        "location": "Saravanampatti, Coimbatore",
        "price": 12000000,
        "land_size": "2400 sq ft",
        "description": "Stunning independent villa with private garden, swimming pool and premium interiors. Perfect for luxury family living.",
        "style": "luxury",
        "rooms": ["luxury living room interior", "luxury bedroom interior", "luxury kitchen interior", "luxury bathroom interior"]
    },
    {
        "title": "Minimalist Studio Apartment",
        "location": "Koramangala, Bangalore",
        "price": 4500000,
        "land_size": "650 sq ft",
        "description": "Beautifully designed minimalist studio in the heart of Koramangala. Perfect for young professionals.",
        "style": "minimalist",
        "rooms": ["minimalist living room", "minimalist bedroom", "minimalist kitchen", "minimalist bathroom"]
    },
    {
        "title": "Farmhouse Style Home",
        "location": "Vijayanagar, Mysore",
        "price": 6800000,
        "land_size": "3200 sq ft",
        "description": "Charming farmhouse home with exposed brick walls, wooden flooring and large backyard. A rare find.",
        "style": "farmhouse",
        "rooms": ["farmhouse living room interior", "farmhouse bedroom interior", "farmhouse kitchen interior", "farmhouse bathroom"]
    },
    {
        "title": "Traditional 4BHK Family Home",
        "location": "Anna Nagar, Madurai",
        "price": 5500000,
        "land_size": "2800 sq ft",
        "description": "Beautiful traditional home with classic architecture, spacious rooms and peaceful courtyard.",
        "style": "traditional",
        "rooms": ["traditional living room interior", "traditional bedroom interior", "traditional kitchen interior", "traditional bathroom interior"]
    },
    {
        "title": "Modern 2BHK in IT Hub",
        "location": "Gachibowli, Hyderabad",
        "price": 7200000,
        "land_size": "1200 sq ft",
        "description": "Contemporary flat in the IT hub of Hyderabad. Modern amenities, gym, pool and 24/7 security.",
        "style": "modern",
        "rooms": ["modern apartment living room", "modern apartment bedroom", "modern apartment kitchen", "modern apartment bathroom"]
    },
    {
        "title": "Scandinavian Style 3BHK",
        "location": "Banjara Hills, Hyderabad",
        "price": 9500000,
        "land_size": "1600 sq ft",
        "description": "Elegant Scandinavian design with clean lines, natural light and premium finishes throughout.",
        "style": "scandinavian",
        "rooms": ["scandinavian living room interior", "scandinavian bedroom interior", "scandinavian kitchen interior", "scandinavian bathroom interior"]
    },
    {
        "title": "Industrial Loft Apartment",
        "location": "Bandra, Mumbai",
        "price": 15000000,
        "land_size": "1100 sq ft",
        "description": "Stunning industrial loft with exposed brick, high ceilings and premium city views. A designer's dream.",
        "style": "industrial",
        "rooms": ["industrial loft living room", "industrial bedroom interior", "industrial kitchen interior", "industrial bathroom interior"]
    },
    {
        "title": "Bohemian 2BHK Garden Flat",
        "location": "Indiranagar, Bangalore",
        "price": 5800000,
        "land_size": "950 sq ft",
        "description": "Vibrant bohemian apartment with lush garden access, colorful interiors and artistic touches throughout.",
        "style": "bohemian",
        "rooms": ["bohemian living room interior", "bohemian bedroom interior", "bohemian kitchen interior", "bohemian bathroom interior"]
    },
    {
        "title": "Luxury Penthouse with Terrace",
        "location": "Jubilee Hills, Hyderabad",
        "price": 25000000,
        "land_size": "3500 sq ft",
        "description": "Breathtaking penthouse with panoramic city views, private terrace, home theatre and premium smart home features.",
        "style": "luxury",
        "rooms": ["luxury penthouse living room", "luxury penthouse bedroom", "luxury penthouse kitchen", "luxury penthouse bathroom"]
    }
]

ROOM_TYPES = ["living room", "bedroom", "kitchen", "bathroom"]

def seed():
    # Clear old demo data
    properties_collection.delete_many({"seller_id": "demo_seed"})
    images_collection.delete_many({"seller_id": "demo_seed"})
    print("Cleared old demo data...")

    for prop in demo_properties:
        rooms = prop.pop("rooms")
        style = prop.pop("style")

        # Fetch images from Unsplash for each room
        all_image_urls = []
        room_info_list = []

        print(f"Fetching images for: {prop['title']}")

        for i, room_query in enumerate(rooms):
            urls = fetch_images(room_query, count=2)
            room_type = ROOM_TYPES[i]
            for url in urls:
                all_image_urls.append(url)
                room_info_list.append({
                    "room_type": room_type,
                    "style": style
                })

        prop["images"] = all_image_urls
        prop["seller_id"] = "demo_seed"
        prop["views"] = random.randint(20, 200)
        prop["likes"] = random.randint(5, 80)
        prop["comments"] = [
            {"user": "Rahul", "text": "Looks amazing!"},
            {"user": "Priya", "text": "Love the design!"}
        ]

        # Insert property
        result = properties_collection.insert_one(prop)
        property_id = str(result.inserted_id)

        # Insert images with room metadata
        for url, room_info in zip(all_image_urls, room_info_list):
            image_doc = {
                "property_id": property_id,
                "seller_id": "demo_seed",
                "url": url,
                "cloudinary_id": f"demo_{property_id}",
                "room_type": room_info["room_type"],
                "style": room_info["style"],
                "group": f"group_{ROOM_TYPES.index(room_info['room_type'])}",
                "quality_score": 95,
                "views": 0,
                "likes": 0,
                "comments": []
            }
            images_collection.insert_one(image_doc)

        print(f"  ✅ {len(all_image_urls)} images added")

    print(f"\n🎉 Seeded {len(demo_properties)} properties with real Unsplash images!")

if __name__ == "__main__":
    seed()
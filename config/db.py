from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["real_estate_ai"]

# Collections
users_collection = db["users"]
properties_collection = db["properties"]
images_collection = db["images"]
partnership_codes_collection = db["partnership_codes"]

def get_db():
    return db

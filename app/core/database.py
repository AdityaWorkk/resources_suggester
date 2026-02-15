from pymongo import MongoClient
from .config import settings
import sys

class Database:
    def __init__(self):
        try:
            self.client = MongoClient(settings.MONGO_URI)
            self.db = self.client[settings.DB_NAME]
            # Test connection
            self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)

    def get_collection(self, name: str):
        return self.db[name]

# Instantiate the singleton
db = Database()

# Helpers to get specific collections easily
users_col = db.get_collection("users")
collections_col = db.get_collection("user_collections")


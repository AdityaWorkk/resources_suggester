import bcrypt
from app.core.database import users_col, collections_col
from bson import ObjectId

class DBService:
    @staticmethod
    def hash_password(password: str) -> str:
        # Slice to 70 chars to prevent bcrypt 72-byte overflow issues
        safe_password = password[:70].encode('utf-8')
        return bcrypt.hashpw(safe_password, bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        # Must slice during verification as well to match the original hash
        safe_password = password[:70].encode('utf-8')
        return bcrypt.checkpw(safe_password, hashed.encode('utf-8'))

    @staticmethod
    def add_to_collection(user_id: str, resource_data: dict):
        """
        Adds a resource to the user's collection with a hard limit of 5.
        """
        user_id_obj = ObjectId(user_id)
        
        # Check current count for the specific user
        count = collections_col.count_documents({"user_id": user_id_obj})
        
        if count >= 5:
            return False, "Collection is full (Max 5 items)"
        
        resource_data["user_id"] = user_id_obj
        collections_col.insert_one(resource_data)
        return True, "Added to collection"

    @staticmethod
    def delete_from_collection(user_id: str, resource_id: str):
        """
        Deletes a specific resource from a user's collection.
        """
        result = collections_col.delete_one({
            "_id": ObjectId(resource_id),
            "user_id": ObjectId(user_id)
        })
        return result.deleted_count > 0
    
from flask import Blueprint, request, jsonify
from app.core.database import users_col,collections_col
from app.v1.endpoints.schemas import UserRegister, UserLogin
from app.v1.services.db_service import DBService
from app.core.config import settings
import jwt
import datetime
from pydantic import ValidationError
from app.v1.middleware.auth import token_required
from app.v1.services.ai_service import ai_engine
from bson import ObjectId
import json

# Define the blueprint
v1_api = Blueprint('v1_api', __name__)

@v1_api.route('/register', methods=['POST'])
def register():
    try:
        # Validate input with Pydantic
        data = UserRegister(**request.json)
        
        # Check if user exists
        if users_col.find_one({"$or": [{"username": data.username}, {"email": data.email}]}):
            return jsonify({"status": "error", "message": "User already exists"}), 400
        
        # Create user document
        user_doc = {
            "username": data.username,
            "email": data.email,
            "password": DBService.hash_password(data.password),
            "is_active": True,
            "termination_reason": "",
            "created_at": datetime.datetime.utcnow()
        }
        
        users_col.insert_one(user_doc)
        return jsonify({"status": "success", "message": "User registered successfully"}), 201
    
    except ValidationError as e:
        return jsonify({"status": "error", "message": e.errors()}), 400

@v1_api.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400

    user = users_col.find_one({"username": username})
    
    # 1. Verify user exists and password is valid
    if user and DBService.verify_password(password, user['password']):
        
        # 2. Check if account is active (Banned/Terminated check)
        if not user.get('is_active', True):
            reason = user.get('termination_reason', "No specific reason provided.")
            return jsonify({
                "status": "error", 
                "message": f"Account deactivated. Reason: {reason}"
            }), 403
            
        # 3. Create JWT with 24-hour expiration
        # 'exp' must be a UTC timestamp for PyJWT to validate it correctly
        payload = {
            'user_id': str(user['_id']),
            'iat': datetime.datetime.utcnow(),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        
        token = jwt.encode(
            payload, 
            settings.JWT_SECRET, 
            algorithm=settings.JWT_ALGORITHM
        )
        
        return jsonify({
            "status": "success",
            "token": token,
            "username": user['username']
        })
    
    return jsonify({"status": "error", "message": "Invalid username or password"}), 401

@v1_api.route('/chat', methods=['POST'])
@token_required
def chat(current_user):
    data = request.json
    category = data.get('category', 'General')
    prompt = data.get('prompt')

    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required"}), 400

    raw_ai_response = ai_engine.get_suggestions(category, prompt)
    
    try:
        # Gemini returns a string, we parse it into a Python list
        suggestions = json.loads(raw_ai_response)
        return jsonify({"status": "success", "data": suggestions})
    except Exception as e:
        return jsonify({"status": "error", "message": "AI returned invalid format", "raw": raw_ai_response}), 500

@v1_api.route('/collection', methods=['POST'])
@token_required
def add_to_my_collection(current_user):
    resource_data = request.json # Expecting name, description, rating, link, category
    
    success, message = DBService.add_to_collection(str(current_user['_id']), resource_data)
    
    if success:
        return jsonify({"status": "success", "message": message}), 201
    return jsonify({"status": "error", "message": message}), 400

@v1_api.route('/collection', methods=['GET'])
@token_required
def get_my_collection(current_user):
    resources = list(collections_col.find({"user_id": current_user['_id']}))
    # Convert MongoDB ObjectId to string for JSON serialization
    for res in resources:
        res['_id'] = str(res['_id'])
        res['user_id'] = str(res['user_id'])
        
    return jsonify({"status": "success", "data": resources})

@v1_api.route('/collection/<resource_id>', methods=['DELETE'])
@token_required
def delete_resource(current_user, resource_id):
    success = DBService.delete_from_collection(str(current_user['_id']), resource_id)
    if success:
        return jsonify({"status": "success", "message": "Resource deleted"})
    return jsonify({"status": "error", "message": "Resource not found or unauthorized"}), 404

@v1_api.route('/admin/users', methods=['GET'])
def get_all_users():
    # In a real app, you'd protect this with an Admin JWT
    users = list(users_col.find({}, {"password": 0})) # Don't send passwords!
    for u in users:
        u['_id'] = str(u['_id'])
    return jsonify({"status": "success", "data": users})

@v1_api.route('/admin/terminate', methods=['POST'])
def terminate_user():
    data = request.json
    user_id = data.get('user_id')
    reason = data.get('reason')

    if not user_id or not reason:
        return jsonify({"status": "error", "message": "User ID and Reason are required"}), 400

    result = users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": False, "termination_reason": reason}}
    )

    if result.modified_count > 0:
        return jsonify({"status": "success", "message": f"User {user_id} terminated."})
    return jsonify({"status": "error", "message": "User not found"}), 404

@v1_api.route('/me', methods=['DELETE'])
@token_required
def delete_self(current_user):
    # 1. Delete user's collection
    collections_col.delete_many({"user_id": current_user['_id']})
    # 2. Delete the user
    users_col.delete_one({"_id": current_user['_id']})
    
    return jsonify({"status": "success", "message": "Account and data deleted successfully"})





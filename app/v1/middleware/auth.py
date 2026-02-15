import jwt
from functools import wraps
from flask import request, jsonify
from app.core.config import settings
from app.core.database import users_col
from bson import ObjectId

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"status": "error", "message": "Token is missing"}), 401

        try:
            # Handle 'Bearer <token>' format
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            
            # jwt.decode automatically validates the 'exp' claim inside the payload
            data = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            
            current_user = users_col.find_one({"_id": ObjectId(data['user_id'])})
            
            if not current_user:
                return jsonify({"status": "error", "message": "User not found"}), 401
            
            # Check if account is active (for Admin terminations)
            if not current_user.get('is_active', True):
                reason = current_user.get('termination_reason', 'No reason provided')
                return jsonify({
                    "status": "error", 
                    "message": f"Account deactivated by Admin. Reason: {reason}"
                }), 403

        except jwt.ExpiredSignatureError:
            # Specific handling for expired tokens
            return jsonify({"status": "error", "message": "Token has expired. Please login again."}), 401
        
        except jwt.InvalidTokenError:
            # Handling for malformed or tampered tokens
            return jsonify({"status": "error", "message": "Invalid token. Access denied."}), 401
            
        except Exception as e:
            # Catch-all for unexpected errors (e.g., ObjectId conversion failure)
            return jsonify({"status": "error", "message": "Authentication failed"}), 401

        return f(current_user, *args, **kwargs)

    return decorated


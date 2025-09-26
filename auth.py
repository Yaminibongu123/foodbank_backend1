from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import User
import logging

logger = logging.getLogger(__name__)
jwt = JWTManager()

def init_auth(app):
    jwt.init_app(app)

@jwt.user_identity_loader
def user_identity_lookup(user):
    return user.id

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.find_by_id(identity)

def authenticate_user(username, password):
    try:
        logger.info(f"Attempting to authenticate user: {username}")
        
        # Try to find user by username first, then by email
        user = User.find_by_username(username)
        if not user:
            user = User.find_by_email(username)
            logger.info(f"User not found by username, trying email: {username}")
        
        if not user:
            logger.error(f"User not found: {username}")
            return None
            
        logger.info(f"User found: {user.username}, ID: {user.id}")
        logger.info(f"Stored password hash: {user.password_hash}")
        
        # Verify password
        password_valid = user.verify_password(password)
        logger.info(f"Password verification result: {password_valid}")
        
        if password_valid:
            logger.info("Authentication successful")
            return user
        else:
            logger.error("Password verification failed")
            return None
            
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        return None

def create_tokens(user):
    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    return access_token, refresh_token
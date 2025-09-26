from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import User, FoodDonation, FoodRequest, OTPVerification
from auth import authenticate_user, create_tokens
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

# Root endpoint
@api.route('/')
def api_root():
    """API root endpoint showing available routes"""
    return jsonify({
        'message': 'Food Bank API is running successfully!',
        'version': '1.0',
        'endpoints': {
            'auth': {
                'register': 'POST /api/auth/register',
                'login': 'POST /api/auth/login',
                'refresh': 'POST /api/auth/refresh',
                'forgot_password': 'POST /api/auth/forgot-password',
                'reset_password': 'POST /api/auth/reset-password',
                'status': 'GET /api/auth/status'
            },
            'profile': {
                'get_profile': 'GET /api/profile',
                'update_profile': 'PUT /api/profile'
            },
            'donations': {
                'create_donation': 'POST /api/donations',
                'get_donations': 'GET /api/donations'
            },
            'otp': {
                'send_otp': 'POST /api/otp/send',
                'verify_otp': 'POST /api/otp/verify'
            },
            'inventory': {
                'get_inventory': 'GET /api/inventory'
            }
        }
    })

# Health check endpoint
@api.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0'
    })

# Auth status endpoint
@api.route('/auth/status')
def auth_status():
    """Check authentication system status"""
    return jsonify({
        'status': 'Authentication system is active',
        'timestamp': datetime.now().isoformat(),
        'system': 'operational'
    })

# Auth routes
@api.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Check if user already exists
        if User.find_by_username(data.get('username')):
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.find_by_email(data.get('email')):
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=User.hash_password(data.get('password')),
            full_name=data.get('full_name'),
            phone=data.get('phone'),
            role=data.get('role', 'donor')
        )
        
        if user.save():
            access_token, refresh_token = create_tokens(user)
            return jsonify({
                'message': 'User registered successfully',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            }), 201
        
        return jsonify({'error': 'Failed to create user'}), 500
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        logger.info(f"Login attempt with data: {data}")
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            logger.error("Missing username or password")
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = authenticate_user(data.get('username'), data.get('password'))
        
        if user:
            access_token, refresh_token = create_tokens(user)
            
            # Update last login
            user.last_login = datetime.now()
            user.save()
            
            logger.info(f"Login successful for user: {user.username}")
            return jsonify({
                'message': 'Login successful',
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.to_dict()
            })
        
        logger.error(f"Login failed for user: {data.get('username')}")
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/auth/debug/users', methods=['GET'])
def debug_users():
    """Debug endpoint to check users in database"""
    try:
        # This is a temporary debug endpoint - remove in production
        users = []
        # You'll need to implement a method to get all users
        # For now, let's just return a message
        return jsonify({
            'message': 'Debug endpoint - implement user listing if needed',
            'warning': 'Remove this endpoint in production'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
# Profile routes
@api.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({'user': user.to_dict()})
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        data = request.get_json()
        
        # Update allowed fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.find_by_email(data['email'])
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Email already taken'}), 400
            user.email = data['email']
            
        if user.save():
            return jsonify({
                'message': 'Profile updated successfully',
                'user': user.to_dict()
            })
            
        return jsonify({'error': 'Failed to update profile'}), 500
        
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Donations routes
@api.route('/donations', methods=['GET'])
@jwt_required()
def get_donations():
    """Get all donations (with optional filtering)"""
    try:
        # Get query parameters for filtering
        status = request.args.get('status')
        donor_id = request.args.get('donor_id')
        
        if donor_id:
            donations = FoodDonation.find_by_donor(donor_id)
        elif status:
            donations = FoodDonation.find_by_status(status)
        else:
            donations = FoodDonation.get_all_donations()
        
        donations_list = []
        for donation in donations:
            donations_list.append({
                'id': donation.id,
                'food_item': donation.food_item,
                'quantity': donation.quantity,
                'expiry_date': donation.expiry_date.isoformat() if donation.expiry_date else None,
                'donor_id': donation.donor_id,
                'status': donation.status,
                'created_at': donation.created_at.isoformat() if donation.created_at else None
            })
        
        return jsonify({
            'donations': donations_list,
            'count': len(donations_list)
        })
        
    except Exception as e:
        logger.error(f"Get donations error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/donations', methods=['POST'])
@jwt_required()
def create_donation():
    """Create a new food donation"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['food_item', 'quantity']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create new donation
        donation = FoodDonation(
            food_item=data.get('food_item'),
            quantity=data.get('quantity'),
            expiry_date=datetime.fromisoformat(data.get('expiry_date')) if data.get('expiry_date') else None,
            donor_id=current_user_id,
            status='available',
            description=data.get('description')
        )
        
        if donation.save():
            return jsonify({
                'message': 'Donation created successfully',
                'donation': {
                    'id': donation.id,
                    'food_item': donation.food_item,
                    'quantity': donation.quantity,
                    'expiry_date': donation.expiry_date.isoformat() if donation.expiry_date else None,
                    'donor_id': donation.donor_id,
                    'status': donation.status
                }
            }), 201
        
        return jsonify({'error': 'Failed to create donation'}), 500
        
    except Exception as e:
        logger.error(f"Create donation error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Inventory route
@api.route('/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    """Get food inventory (available donations)"""
    try:
        # Get all available donations
        donations = FoodDonation.get_available_donations()
        
        inventory = []
        for donation in donations:
            inventory.append({
                'id': donation.id,
                'food_item': donation.food_item,
                'quantity': donation.quantity,
                'expiry_date': donation.expiry_date.isoformat() if donation.expiry_date else None,
                'donor_id': donation.donor_id,
                'status': donation.status,
                'description': donation.description
            })
        
        return jsonify({
            'inventory': inventory,
            'count': len(inventory)
        })
        
    except Exception as e:
        logger.error(f"Inventory error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# OTP routes
@api.route('/otp/send', methods=['POST'])
def send_otp():
    """Send OTP for verification"""
    try:
        data = request.get_json()
        
        if not data.get('phone'):
            return jsonify({'error': 'Phone number is required'}), 400
            
        # Your OTP sending logic here
        otp = OTPVerification.generate_otp(data.get('phone'))
        
        return jsonify({
            'message': 'OTP sent successfully',
            'otp_id': otp.id  # For testing, in production you wouldn't return this
        })
        
    except Exception as e:
        logger.error(f"Send OTP error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/otp/verify', methods=['POST'])
def verify_otp():
    """Verify OTP"""
    try:
        data = request.get_json()
        
        required_fields = ['otp_id', 'otp_code']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        is_verified = OTPVerification.verify_otp(data.get('otp_id'), data.get('otp_code'))
        
        if is_verified:
            return jsonify({'message': 'OTP verified successfully'})
        else:
            return jsonify({'error': 'Invalid OTP'}), 400
        
    except Exception as e:
        logger.error(f"Verify OTP error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Token refresh endpoint
@api.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.find_by_id(current_user_id)
        
        if user:
            access_token = create_access_token(identity=current_user_id)
            return jsonify({
                'access_token': access_token
            })
        
        return jsonify({'error': 'User not found'}), 404
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Password reset endpoints (simplified versions)
@api.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Initiate password reset"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return jsonify({'error': 'Email is required'}), 400
            
        user = User.find_by_email(data.get('email'))
        if user:
            # In a real app, you'd send an email with reset link
            return jsonify({'message': 'Password reset instructions sent to your email'})
        else:
            # For security, don't reveal if email exists or not
            return jsonify({'message': 'If the email exists, reset instructions have been sent'})
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.get_json()
        
        required_fields = ['token', 'new_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # In a real app, you'd verify the token and update password
        return jsonify({'message': 'Password reset successfully'})
        
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
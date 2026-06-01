"""Authentication routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    if not data:
        return {'error': 'No data provided'}, 400
    
    # Validate input
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return {'error': 'Username, email, and password are required'}, 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return {'error': 'Username already exists'}, 409
    
    if User.query.filter_by(email=data['email']).first():
        return {'error': 'Email already exists'}, 409
    
    # Create new user
    user = User(
        username=data['username'],
        email=data['email'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return {
        'message': 'User registered successfully',
        'user': user.to_dict(include_email=True),
        'access_token': access_token
    }, 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return {'error': 'Email and password are required'}, 400
    
    # Find user
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return {'error': 'Invalid email or password'}, 401
    
    if not user.is_active:
        return {'error': 'User account is inactive'}, 403
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return {
        'message': 'Login successful',
        'user': user.to_dict(include_email=True),
        'access_token': access_token
    }, 200

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return {'error': 'User not found'}, 404
    
    return {
        'user': user.to_dict(include_email=True),
        'installed_apps_count': len(user.installed_apps),
        'wishlist_count': len(user.wishlist_items),
    }, 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return {'error': 'User not found'}, 404
    
    data = request.get_json()
    
    # Update fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'bio' in data:
        user.bio = data['bio']
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    
    user.updated_at = datetime.utcnow()
    db.session.commit()
    
    return {'message': 'Profile updated successfully', 'user': user.to_dict()}, 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return {'error': 'User not found'}, 404
    
    data = request.get_json()
    
    if not data.get('old_password') or not data.get('new_password'):
        return {'error': 'Old password and new password are required'}, 400
    
    if not user.check_password(data['old_password']):
        return {'error': 'Invalid old password'}, 401
    
    user.set_password(data['new_password'])
    db.session.commit()
    
    return {'message': 'Password changed successfully'}, 200

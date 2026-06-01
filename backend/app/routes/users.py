"""User routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Installation, Wishlist

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/installed', methods=['GET'])
@jwt_required()
def get_installed_apps():
    """Get user's installed apps"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    installations = Installation.query.filter_by(user_id=user_id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return {
        'apps': [{'id': inst.app.id,
            'name': inst.app.name,
            'icon_url': inst.app.icon_url,
            'version': inst.version,
            'installed_at': inst.installed_at.isoformat(),
            'updated_at': inst.updated_at.isoformat(),
        } for inst in installations.items],
        'total': installations.total,
        'pages': installations.pages,
        'current_page': page,
    }, 200

@users_bp.route('/wishlist', methods=['GET'])
@jwt_required()
def get_wishlist():
    """Get user's wishlist"""
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    wishlist = Wishlist.query.filter_by(user_id=user_id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return {
        'apps': [{'id': wish.app.id,
            'name': wish.app.name,
            'icon_url': wish.app.icon_url,
            'price': wish.app.price,
            'rating': wish.app.rating,
            'category': wish.app.category,
            'added_at': wish.added_at.isoformat(),
        } for wish in wishlist.items],
        'total': wishlist.total,
        'pages': wishlist.pages,
        'current_page': page,
    }, 200

@users_bp.route('/<username>', methods=['GET'])
def get_user_profile(username):
    """Get public user profile"""
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return {'error': 'User not found'}, 404
    
    return {
        'user': user.to_dict(),
        'apps_published': len(user.apps),
        'reviews_count': len(user.reviews),
        'member_since': user.created_at.isoformat(),
    }, 200

"""Admin routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, App
from datetime import datetime
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(f):
    """Check if user is admin"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return {'error': 'Admin access required'}, 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/apps', methods=['GET'])
@admin_required
def get_all_apps():
    """Get all apps (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '', type=str)
    
    query = App.query
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'apps': [app.to_dict() for app in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }, 200

@admin_bp.route('/apps/<app_id>/approve', methods=['PUT'])
@admin_required
def approve_app(app_id):
    """Approve an app"""
    app = App.query.get(app_id)
    
    if not app:
        return {'error': 'App not found'}, 404
    
    app.is_active = True
    db.session.commit()
    
    return {'message': 'App approved successfully'}, 200

@admin_bp.route('/apps/<app_id>/reject', methods=['PUT'])
@admin_required
def reject_app(app_id):
    """Reject/disable an app"""
    app = App.query.get(app_id)
    
    if not app:
        return {'error': 'App not found'}, 404
    
    app.is_active = False
    db.session.commit()
    
    return {'message': 'App disabled successfully'}, 200

@admin_bp.route('/apps/<app_id>/feature', methods=['PUT'])
@admin_required
def toggle_featured(app_id):
    """Toggle featured status of app"""
    app = App.query.get(app_id)
    
    if not app:
        return {'error': 'App not found'}, 404
    
    app.is_featured = not app.is_featured
    db.session.commit()
    
    return {
        'message': f"App {'featured' if app.is_featured else 'unfeatured'} successfully"
    }, 200

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role', '', type=str)
    
    query = User.query
    
    if role == 'admin':
        query = query.filter_by(is_admin=True)
    elif role == 'user':
        query = query.filter_by(is_admin=False)
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'users': [user.to_dict(include_email=True) for user in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }, 200

@admin_bp.route('/users/<user_id>/make-admin', methods=['PUT'])
@admin_required
def make_admin(user_id):
    """Make user an admin"""
    user = User.query.get(user_id)
    
    if not user:
        return {'error': 'User not found'}, 404
    
    user.is_admin = True
    db.session.commit()
    
    return {'message': 'User promoted to admin'}, 200

@admin_bp.route('/users/<user_id>/remove-admin', methods=['PUT'])
@admin_required
def remove_admin(user_id):
    """Remove admin status from user"""
    user = User.query.get(user_id)
    
    if not user:
        return {'error': 'User not found'}, 404
    
    user.is_admin = False
    db.session.commit()
    
    return {'message': 'Admin status removed'}, 200

@admin_bp.route('/users/<user_id>/disable', methods=['PUT'])
@admin_required
def disable_user(user_id):
    """Disable a user account"""
    user = User.query.get(user_id)
    
    if not user:
        return {'error': 'User not found'}, 404
    
    user.is_active = False
    db.session.commit()
    
    return {'message': 'User account disabled'}, 200

@admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """Get platform statistics"""
    total_users = User.query.count()
    total_apps = App.query.count()
    total_active_apps = App.query.filter_by(is_active=True).count()
    total_downloads = db.session.query(db.func.sum(App.download_count)).scalar() or 0
    
    return {
        'total_users': total_users,
        'total_apps': total_apps,
        'total_active_apps': total_active_apps,
        'total_downloads': total_downloads,
    }, 200

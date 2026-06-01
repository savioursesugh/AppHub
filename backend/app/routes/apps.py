"""App routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import App, Installation, Review, Wishlist
from sqlalchemy import func

apps_bp = Blueprint('apps', __name__, url_prefix='/api/apps')

@apps_bp.route('', methods=['GET'])
def get_apps():
    """Get apps with filtering, searching, and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    category = request.args.get('category', '', type=str)
    sort_by = request.args.get('sort_by', 'rating', type=str)
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 10000, type=float)
    min_rating = request.args.get('min_rating', 0, type=float)
    is_featured = request.args.get('featured', 'false', type=str).lower() == 'true'
    
    query = App.query.filter_by(is_active=True)
    
    # Search by name or description
    if search:
        query = query.filter(
            (App.name.ilike(f'%{search}%')) |
            (App.description.ilike(f'%{search}%'))
        )
    
    # Filter by category
    if category:
        query = query.filter_by(category=category)
    
    # Filter by price range
    query = query.filter(App.price.between(min_price, max_price))
    
    # Filter by rating
    query = query.filter(App.rating >= min_rating)
    
    # Filter featured
    if is_featured:
        query = query.filter_by(is_featured=True)
    
    # Sort
    if sort_by == 'downloads':
        query = query.order_by(App.download_count.desc())
    elif sort_by == 'newest':
        query = query.order_by(App.created_at.desc())
    elif sort_by == 'price':
        query = query.order_by(App.price.asc())
    else:  # rating
        query = query.order_by(App.rating.desc())
    
    # Paginate
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'apps': [app.to_dict() for app in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }, 200

@apps_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all app categories"""
    categories = db.session.query(App.category, func.count(App.id)).filter_by(is_active=True).group_by(App.category).all()
    return {
        'categories': [
            {'name': cat[0], 'count': cat[1]} for cat in categories if cat[0]
        ]
    }, 200

@apps_bp.route('/<app_id>', methods=['GET'])
def get_app(app_id):
    """Get single app details"""
    app = App.query.get(app_id)
    
    if not app or not app.is_active:
        return {'error': 'App not found'}, 404
    
    # Get reviews
    reviews = Review.query.filter_by(app_id=app_id).all()
    
    return {
        'app': app.to_dict(),
        'reviews': [review.to_dict() for review in reviews],
        'total_reviews': len(reviews),
    }, 200

@apps_bp.route('/<app_id>/install', methods=['POST'])
@jwt_required()
def install_app(app_id):
    """Install app"""
    user_id = get_jwt_identity()
    app = App.query.get(app_id)
    
    if not app:
        return {'error': 'App not found'}, 404
    
    # Check if already installed
    existing = Installation.query.filter_by(user_id=user_id, app_id=app_id).first()
    if existing:
        return {'error': 'App already installed'}, 409
    
    # Create installation
    installation = Installation(
        user_id=user_id,
        app_id=app_id,
        version=app.version
    )
    
    app.download_count += 1
    db.session.add(installation)
    db.session.commit()
    
    return {'message': 'App installed successfully'}, 201

@apps_bp.route('/<app_id>/uninstall', methods=['POST'])
@jwt_required()
def uninstall_app(app_id):
    """Uninstall app"""
    user_id = get_jwt_identity()
    
    installation = Installation.query.filter_by(user_id=user_id, app_id=app_id).first()
    
    if not installation:
        return {'error': 'App not installed'}, 404
    
    app = App.query.get(app_id)
    app.download_count = max(0, app.download_count - 1)
    
    db.session.delete(installation)
    db.session.commit()
    
    return {'message': 'App uninstalled successfully'}, 200

@apps_bp.route('/<app_id>/wishlist', methods=['POST'])
@jwt_required()
def add_to_wishlist(app_id):
    """Add app to wishlist"""
    user_id = get_jwt_identity()
    app = App.query.get(app_id)
    
    if not app:
        return {'error': 'App not found'}, 404
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(user_id=user_id, app_id=app_id).first()
    if existing:
        return {'error': 'Already in wishlist'}, 409
    
    wishlist = Wishlist(user_id=user_id, app_id=app_id)
    db.session.add(wishlist)
    db.session.commit()
    
    return {'message': 'Added to wishlist'}, 201

@apps_bp.route('/<app_id>/wishlist', methods=['DELETE'])
@jwt_required()
def remove_from_wishlist(app_id):
    """Remove app from wishlist"""
    user_id = get_jwt_identity()
    
    wishlist = Wishlist.query.filter_by(user_id=user_id, app_id=app_id).first()
    
    if not wishlist:
        return {'error': 'Not in wishlist'}, 404
    
    db.session.delete(wishlist)
    db.session.commit()
    
    return {'message': 'Removed from wishlist'}, 200

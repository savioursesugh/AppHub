"""Review routes"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Review, App, Installation
from datetime import datetime
from sqlalchemy import func

reviews_bp = Blueprint('reviews', __name__, url_prefix='/api/reviews')

@reviews_bp.route('/app/<app_id>', methods=['GET'])
def get_app_reviews(app_id):
    """Get reviews for an app"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    sort_by = request.args.get('sort_by', 'newest', type=str)
    rating = request.args.get('rating', '', type=str)
    
    query = Review.query.filter_by(app_id=app_id)
    
    if rating:
        try:
            rating_val = int(rating)
            query = query.filter_by(rating=rating_val)
        except ValueError:
            pass
    
    if sort_by == 'helpful':
        query = query.order_by(Review.helpful_count.desc())
    elif sort_by == 'rating':
        query = query.order_by(Review.rating.desc())
    else:
        query = query.order_by(Review.created_at.desc())
    
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return {
        'reviews': [review.to_dict() for review in paginated.items],
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }, 200

@reviews_bp.route('/app/<app_id>', methods=['POST'])
@jwt_required()
def create_review(app_id):
    """Create a review for an app"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    app = App.query.get(app_id)
    if not app:
        return {'error': 'App not found'}, 404
    
    installation = Installation.query.filter_by(user_id=user_id, app_id=app_id).first()
    if not installation:
        return {'error': 'You must install the app to review it'}, 403
    
    existing = Review.query.filter_by(user_id=user_id, app_id=app_id).first()
    if existing:
        return {'error': 'You have already reviewed this app'}, 409
    
    if not data or not data.get('rating'):
        return {'error': 'Rating is required'}, 400
    
    try:
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return {'error': 'Rating must be between 1 and 5'}, 400
    except ValueError:
        return {'error': 'Invalid rating'}, 400
    
    review = Review(
        user_id=user_id,
        app_id=app_id,
        rating=rating,
        title=data.get('title', ''),
        content=data.get('content', ''),
    )
    
    all_reviews = Review.query.filter_by(app_id=app_id).all()
    all_reviews.append(review)
    avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
    app.rating = round(avg_rating, 1)
    app.reviews_count = len(all_reviews)
    
    db.session.add(review)
    db.session.commit()
    
    return {
        'message': 'Review created successfully',
        'review': review.to_dict()
    }, 201

@reviews_bp.route('/<review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    """Delete a review"""
    user_id = get_jwt_identity()
    review = Review.query.get(review_id)
    
    if not review:
        return {'error': 'Review not found'}, 404
    
    if review.user_id != user_id:
        return {'error': 'You can only delete your own reviews'}, 403
    
    app_id = review.app_id
    app = App.query.get(app_id)
    
    db.session.delete(review)
    
    all_reviews = Review.query.filter_by(app_id=app_id).all()
    if all_reviews:
        avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
        app.rating = round(avg_rating, 1)
    else:
        app.rating = 0
    
    app.reviews_count = len(all_reviews)
    db.session.commit()
    
    return {'message': 'Review deleted successfully'}, 200

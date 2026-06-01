"""Routes package"""
from .auth import auth_bp
from .apps import apps_bp
from .users import users_bp
from .reviews import reviews_bp
from .admin import admin_bp

__all__ = ['auth_bp', 'apps_bp', 'users_bp', 'reviews_bp', 'admin_bp']

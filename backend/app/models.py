"""Database models"""
from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(120))
    last_name = db.Column(db.String(120))
    avatar_url = db.Column(db.String(255))
    bio = db.Column(db.Text)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    installed_apps = db.relationship('Installation', backref='user', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_email=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'created_at': self.created_at.isoformat(),
        }
        if include_email:
            data['email'] = self.email
        return data

class App(db.Model):
    """App model"""
    __tablename__ = 'apps'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False, index=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    long_description = db.Column(db.Text)
    icon_url = db.Column(db.String(255))
    screenshot_urls = db.Column(db.JSON, default=[])
    developer_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    version = db.Column(db.String(20), default='1.0.0')
    category = db.Column(db.String(50), index=True)
    price = db.Column(db.Float, default=0.0)
    rating = db.Column(db.Float, default=0.0)
    download_count = db.Column(db.Integer, default=0)
    reviews_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    size = db.Column(db.String(20))
    min_android_version = db.Column(db.String(20), default='5.0')
    requirements = db.Column(db.JSON, default=[])
    permissions = db.Column(db.JSON, default=[])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    developer = db.relationship('User', backref='apps')
    installations = db.relationship('Installation', backref='app', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='app', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('Wishlist', backref='app', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_developer=True):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'long_description': self.long_description,
            'icon_url': self.icon_url,
            'screenshot_urls': self.screenshot_urls,
            'version': self.version,
            'category': self.category,
            'price': self.price,
            'rating': self.rating,
            'download_count': self.download_count,
            'reviews_count': self.reviews_count,
            'is_featured': self.is_featured,
            'size': self.size,
            'min_android_version': self.min_android_version,
            'requirements': self.requirements,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_developer and self.developer:
            data['developer'] = self.developer.to_dict()
        return data

class Installation(db.Model):
    """Installation model"""
    __tablename__ = 'installations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    app_id = db.Column(db.String(36), db.ForeignKey('apps.id'), nullable=False)
    installed_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = db.Column(db.String(20))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'app_id', name='unique_user_app'),)

class Review(db.Model):
    """Review model"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    app_id = db.Column(db.String(36), db.ForeignKey('apps.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120))
    content = db.Column(db.Text)
    helpful_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'app_id', name='unique_user_app_review'),)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user': self.user.to_dict(),
            'app_id': self.app_id,
            'rating': self.rating,
            'title': self.title,
            'content': self.content,
            'helpful_count': self.helpful_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

class Wishlist(db.Model):
    """Wishlist model"""
    __tablename__ = 'wishlist'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    app_id = db.Column(db.String(36), db.ForeignKey('apps.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'app_id', name='unique_wishlist'),)

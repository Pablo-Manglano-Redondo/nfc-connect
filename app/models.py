# app/models.py
from datetime import datetime
from flask import json
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

# -------------------------------------------------------------------
# Carga de Usuario para Flask-Login
# -------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------------------------------------------
# Modelos de Usuarios
# -------------------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    profile_image = db.Column(db.String(20), nullable=True, default='default.jpg')
    background_image = db.Column(db.String(50), nullable=True, default=None)
    background_video = db.Column(db.String(50), nullable=True, default=None)
    background_type = db.Column(db.String(10), nullable=False, default='image')  # Nuevo campo
    link_color = db.Column(db.String(7), default='#e94e1b')  # Nuevo campo para color de enlaces
    bio = db.Column(db.Text, nullable=True)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Relaciones
    cart = db.relationship('Cart', backref='user', uselist=False, cascade="all, delete-orphan")
    user_links = db.relationship('UserLink', back_populates='owner', lazy='dynamic')
    
    # Métodos para manejar la contraseña
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"

class UserLink(db.Model):
    __tablename__ = 'user_link'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    icon = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    
    # Relaciones
    owner = db.relationship('User', back_populates='user_links')
    
    def __repr__(self):
        return f"<UserLink {self.title} - {self.url}>"

# -------------------------------------------------------------------
# Modelo de Suscripción al Newsletter
# -------------------------------------------------------------------
class NewsletterSubscription(db.Model):
    __tablename__ = 'newsletter_subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_subscribed = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<NewsletterSubscription {self.email}>"

# -------------------------------------------------------------------
# Modelos de Productos
# -------------------------------------------------------------------
class Product(db.Model):
    __tablename__ = 'product'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_file = db.Column(db.String(20), nullable=True, default='default_product.jpg')
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    features = db.Column(db.Text, nullable=True)
    
    # Relaciones
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    images = db.relationship('ProductImage', backref='product', lazy=True)
    
    def get_features_list(self):
        """Devuelve las características como una lista de Python."""
        if self.features:
            try:
                return json.loads(self.features)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_features_list(self, features_list):
        """Establece las características desde una lista de Python."""
        self.features = json.dumps(features_list)
    
    def __repr__(self):
        return f"Product('{self.name}', '${self.price}')"

class ProductImage(db.Model):
    __tablename__ = 'product_image'
    
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(20), nullable=False, default='default_product.jpg')
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    def __repr__(self):
        return f"ProductImage('{self.image_file}')"

# -------------------------------------------------------------------
# Modelos de Carrito de Compras
# -------------------------------------------------------------------
class Cart(db.Model):
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    cart_items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Cart(User ID: {self.user_id})"

class CartItem(db.Model):
    __tablename__ = 'cart_item'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"CartItem(Product ID: {self.product_id}, Quantity: {self.quantity})"

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)

# Set secret key for session management
app.secret_key = os.urandom(24)

# Database Configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

# ==================== MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    password_plain = db.Column(db.String(255), nullable=True)  # Store plain text password for admin viewing
    role = db.Column(db.String(10), nullable=False, default='buyer')  # 'buyer', 'seller', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='buyer', lazy=True)
    cart_items = db.relationship('CartItem', backref='user', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    additional_images = db.Column(db.Text, nullable=True)  # JSON string of image URLs
    video_url = db.Column(db.String(500), nullable=True)  # YouTube/Vimeo embed URL
    stock = db.Column(db.Integer, default=0, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True, cascade='all, delete-orphan')
    wishlist_items = db.relationship('WishlistItem', backref='product', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy=True, cascade='all, delete-orphan')

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Processing, Shipped, Delivered, Cancelled
    shipping_address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Price at time of purchase

class WishlistItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ==================== AUTHENTICATION HELPERS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('login'))
            user = User.query.get(session['user_id'])
            if user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==================== ROUTES ====================

@app.route("/")
def home():
    """Home page with featured products"""
    search_query = request.args.get('search', '').strip()
    category_id = request.args.get('category', type=int)
    
    products_query = Product.query.filter(Product.stock > 0)
    
    if search_query:
        products_query = products_query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%')
            )
        )
    
    if category_id:
        products_query = products_query.filter_by(category_id=category_id)
    
    products = products_query.order_by(Product.created_at.desc()).limit(12).all()
    categories = Category.query.all()
    
    return render_template("index.html", products=products, categories=categories, 
                         search_query=search_query, selected_category=category_id)

@app.route("/register", methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'buyer').strip()
        
        if not all([username, email, password]):
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))
        
        try:
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                password_plain=password,  # Store plain text password for admin viewing
                role=role
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Error during registration. Please try again.', 'danger')
            return redirect(url_for('register'))
    
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not all([username, password]):
            flash('Please enter both username and password.', 'danger')
            return redirect(url_for('login'))
        
        try:
            user = User.query.filter_by(username=username).first()
            
            if not user:
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('login'))
            
            # Check if password_hash exists
            if not user.password_hash:
                flash('Account error. Please contact administrator.', 'danger')
                return redirect(url_for('login'))
            
            if check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role
                flash(f'Welcome back, {user.username}!', 'success')
                
                # Redirect based on role
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'seller':
                    return redirect(url_for('seller_dashboard'))
                else:
                    return redirect(url_for('home'))
            else:
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('login'))
        except Exception as e:
            flash(f'Login error: {str(e)}. Please try again or contact administrator.', 'danger')
            return redirect(url_for('login'))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))

@app.route("/products")
def products():
    """Browse all products"""
    search_query = request.args.get('search', '').strip()
    category_id = request.args.get('category', type=int)
    sort_by = request.args.get('sort', 'newest')  # newest, price_low, price_high
    
    products_query = Product.query.filter(Product.stock > 0)
    
    if search_query:
        products_query = products_query.filter(
            db.or_(
                Product.name.ilike(f'%{search_query}%'),
                Product.description.ilike(f'%{search_query}%')
            )
        )
    
    if category_id:
        products_query = products_query.filter_by(category_id=category_id)
    
    # Sorting
    if sort_by == 'price_low':
        products_query = products_query.order_by(Product.price.asc())
    elif sort_by == 'price_high':
        products_query = products_query.order_by(Product.price.desc())
    else:
        products_query = products_query.order_by(Product.created_at.desc())
    
    products = products_query.all()
    categories = Category.query.all()
    
    return render_template("products.html", products=products, categories=categories,
                         search_query=search_query, selected_category=category_id, sort_by=sort_by)

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    """Product detail page"""
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product_id,
        Product.stock > 0
    ).limit(4).all()

    # Get reviews and calculate average rating
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()
    avg_rating = 0
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)

    return render_template("product_detail.html", product=product, related_products=related_products,
                         reviews=reviews, avg_rating=round(avg_rating, 1))

# ==================== CART ROUTES ====================

@app.route("/cart")
@login_required
def cart():
    """Shopping cart"""
    user_id = session['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    return render_template("cart.html", cart_items=cart_items, total=total)

@app.route("/add_to_cart/<int:product_id>", methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart"""
    user_id = session['user_id']
    quantity = int(request.form.get('quantity', 1))
    
    product = Product.query.get_or_404(product_id)
    
    if product.stock < quantity:
        flash(f'Only {product.stock} items available in stock.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Check if item already in cart
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    
    if cart_item:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            flash(f'Cannot add more. Only {product.stock} items available.', 'warning')
            return redirect(url_for('cart'))
        cart_item.quantity = new_quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route("/update_cart/<int:cart_item_id>", methods=['POST'])
@login_required
def update_cart(cart_item_id):
    """Update cart item quantity"""
    cart_item = CartItem.query.get_or_404(cart_item_id)
    
    if cart_item.user_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('cart'))
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        db.session.delete(cart_item)
    elif quantity > cart_item.product.stock:
        flash(f'Only {cart_item.product.stock} items available.', 'warning')
    else:
        cart_item.quantity = quantity
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route("/remove_from_cart/<int:cart_item_id>", methods=['POST'])
@login_required
def remove_from_cart(cart_item_id):
    """Remove item from cart"""
    cart_item = CartItem.query.get_or_404(cart_item_id)

    if cart_item.user_id != session['user_id']:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('cart'))

    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

# ==================== WISHLIST ROUTES ====================

@app.route("/wishlist")
@login_required
def wishlist():
    """User's wishlist"""
    user_id = session['user_id']
    wishlist_items = WishlistItem.query.filter_by(user_id=user_id).all()

    return render_template("wishlist.html", wishlist_items=wishlist_items)

@app.route("/add_to_wishlist/<int:product_id>", methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Add product to wishlist"""
    user_id = session['user_id']
    product = Product.query.get_or_404(product_id)

    # Check if item already in wishlist
    wishlist_item = WishlistItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if wishlist_item:
        flash(f'{product.name} is already in your wishlist!', 'info')
    else:
        wishlist_item = WishlistItem(user_id=user_id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        flash(f'{product.name} added to wishlist!', 'success')

    return redirect(request.referrer or url_for('product_detail', product_id=product_id))

@app.route("/remove_from_wishlist/<int:product_id>", methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    """Remove product from wishlist"""
    user_id = session['user_id']
    wishlist_item = WishlistItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if wishlist_item:
        product_name = wishlist_item.product.name
        db.session.delete(wishlist_item)
        db.session.commit()
        flash(f'{product_name} removed from wishlist.', 'info')
    else:
        flash('Item not found in wishlist.', 'warning')

    return redirect(request.referrer or url_for('wishlist'))

# ==================== CHECKOUT ROUTES ====================

@app.route("/checkout", methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process"""
    user_id = session['user_id']
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('cart'))
    
    # Check stock availability
    for item in cart_items:
        if item.quantity > item.product.stock:
            flash(f'{item.product.name} has insufficient stock.', 'danger')
            return redirect(url_for('cart'))
    
    if request.method == 'POST':
        shipping_address = request.form.get('shipping_address', '').strip()
        
        if not shipping_address:
            flash('Shipping address is required.', 'danger')
            return render_template("checkout.html", cart_items=cart_items, 
                                 total=sum(item.product.price * item.quantity for item in cart_items))
        
        try:
            # Calculate total
            total = sum(item.product.price * item.quantity for item in cart_items)
            
            # Create order
            order = Order(
                buyer_id=user_id,
                total_amount=total,
                shipping_address=shipping_address,
                status='Pending'
            )
            db.session.add(order)
            db.session.flush()
            
            # Create order items and update stock
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    price=cart_item.product.price
                )
                db.session.add(order_item)
                
                # Update product stock
                cart_item.product.stock -= cart_item.quantity
            
            # Clear cart
            CartItem.query.filter_by(user_id=user_id).delete()
            
            db.session.commit()
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_detail', order_id=order.id))
        except Exception as e:
            db.session.rollback()
            flash('Error processing order. Please try again.', 'danger')
            return redirect(url_for('checkout'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template("checkout.html", cart_items=cart_items, total=total)

@app.route("/orders")
@login_required
def orders():
    """User's order history"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if user.role == 'seller':
        # Seller sees orders for their products
        orders = Order.query.join(OrderItem).join(Product).filter(
            Product.seller_id == user_id
        ).distinct().order_by(Order.created_at.desc()).all()
    else:
        # Buyer sees their own orders
        orders = Order.query.filter_by(buyer_id=user_id).order_by(Order.created_at.desc()).all()
    
    return render_template("orders.html", orders=orders)

@app.route("/order/<int:order_id>")
@login_required
def order_detail(order_id):
    """Order detail page"""
    order = Order.query.get_or_404(order_id)
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Check authorization
    if user.role != 'admin' and user.role != 'seller' and order.buyer_id != user_id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('orders'))
    
    return render_template("order_detail.html", order=order)

@app.route("/update_order_status/<int:order_id>", methods=['POST'])
@login_required
@role_required(['seller', 'admin'])
def update_order_status(order_id):
    """Update order status (seller/admin only)"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', '').strip()
    
    if new_status not in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('order_detail', order_id=order_id))
    
    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    
    flash('Order status updated successfully!', 'success')
    return redirect(url_for('order_detail', order_id=order_id))

# ==================== SELLER ROUTES ====================

@app.route("/seller/dashboard")
@login_required
@role_required(['seller'])
def seller_dashboard():
    """Seller dashboard"""
    user_id = session['user_id']
    products = Product.query.filter_by(seller_id=user_id).order_by(Product.created_at.desc()).all()
    
    # Get sales statistics
    total_products = len(products)
    total_sales = Order.query.join(OrderItem).join(Product).filter(
        Product.seller_id == user_id
    ).count()
    
    return render_template("seller_dashboard.html", products=products, 
                         total_products=total_products, total_sales=total_sales)

@app.route("/seller/add_product", methods=['GET', 'POST'])
@login_required
@role_required(['seller'])
def add_product():
    """Add new product"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        stock = request.form.get('stock', type=int, default=0)
        category_id = request.form.get('category_id', type=int)
        image_url = request.form.get('image_url', '').strip()
        
        if not all([name, price is not None]):
            flash('Name and price are required!', 'danger')
            return redirect(url_for('add_product'))
        
        try:
            product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                category_id=category_id,
                image_url=image_url,
                seller_id=session['user_id']
            )
            db.session.add(product)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('seller_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding product. Please try again.', 'danger')
            return redirect(url_for('add_product'))
    
    categories = Category.query.all()
    return render_template("add_product.html", categories=categories)

@app.route("/seller/edit_product/<int:product_id>", methods=['GET', 'POST'])
@login_required
@role_required(['seller'])
def edit_product(product_id):
    """Edit product"""
    product = Product.query.get_or_404(product_id)
    
    if product.seller_id != session['user_id']:
        flash('You can only edit your own products.', 'danger')
        return redirect(url_for('seller_dashboard'))
    
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.price = request.form.get('price', type=float)
        product.stock = request.form.get('stock', type=int, default=0)
        product.category_id = request.form.get('category_id', type=int)
        product.image_url = request.form.get('image_url', '').strip()
        
        try:
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('seller_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'danger')
            return redirect(url_for('edit_product', product_id=product_id))
    
    categories = Category.query.all()
    return render_template("edit_product.html", product=product, categories=categories)

@app.route("/seller/delete_product/<int:product_id>", methods=['POST'])
@login_required
@role_required(['seller'])
def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)
    
    if product.seller_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product deleted successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== ADMIN ROUTES ====================

@app.route("/admin/dashboard")
@login_required
@role_required(['admin'])
def admin_dashboard():
    """Admin dashboard"""
    users = User.query.all()
    products = Product.query.all()
    orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    categories = Category.query.all()
    
    stats = {
        'total_users': len(users),
        'total_products': len(products),
        'total_orders': Order.query.count(),
        'total_revenue': sum(order.total_amount for order in Order.query.filter_by(status='Delivered').all())
    }
    
    return render_template("admin_dashboard.html", users=users, products=products, 
                         orders=orders, categories=categories, stats=stats)

@app.route("/admin/add_category", methods=['POST'])
@login_required
@role_required(['admin'])
def add_category():
    """Add new category"""
    name = request.form.get('name', '').strip()
    
    if not name:
        flash('Category name is required!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if Category.query.filter_by(name=name).first():
        flash('Category already exists!', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    try:
        category = Category(name=name)
        db.session.add(category)
        db.session.commit()
        flash('Category added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error adding category.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/delete_category/<int:category_id>", methods=['POST'])
@login_required
@role_required(['admin'])
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash('Category deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting category.', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route("/admin/edit_product/<int:product_id>", methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def admin_edit_product(product_id):
    """Admin edit product"""
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        product.description = request.form.get('description', '').strip()
        product.price = request.form.get('price', type=float)
        product.stock = request.form.get('stock', type=int, default=0)
        product.category_id = request.form.get('category_id', type=int)
        product.image_url = request.form.get('image_url', '').strip()
        
        if not product.name or product.price is None:
            flash('Name and price are required!', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))
        
        try:
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'danger')
            return redirect(url_for('admin_edit_product', product_id=product_id))
    
    categories = Category.query.all()
    return render_template("admin_edit_product.html", product=product, categories=categories)

# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_cart_count():
    """Make cart count available in all templates"""
    cart_count = 0
    try:
        if 'user_id' in session:
            cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
    except Exception:
        # Database not initialized or outside request context
        pass
    return dict(cart_count=cart_count)

# ==================== DIAGNOSTIC ROUTES ====================

@app.route("/check_admin")
def check_admin():
    """Check admin accounts in database (for debugging)"""
    try:
        admins = User.query.filter_by(role='admin').all()
        result = []
        for admin in admins:
            # Test if password works
            password_works = check_password_hash(admin.password_hash, 'admin123') if admin.password_hash else False
            result.append({
                'id': admin.id,
                'username': admin.username,
                'email': admin.email,
                'role': admin.role,
                'created_at': str(admin.created_at),
                'password_works': password_works,
                'has_password_hash': bool(admin.password_hash),
                'password_hash_preview': admin.password_hash[:30] + '...' if admin.password_hash else 'None'
            })
        return jsonify({'admins': result, 'count': len(result)})
    except Exception as e:
        return jsonify({'error': str(e), 'admins': [], 'count': 0}), 500

@app.route("/test_login/<username>/<password>")
def test_login(username, password):
    """Test login credentials (for debugging)"""
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({
                'success': False,
                'message': f'User "{username}" not found',
                'user_exists': False
            })
        
        if not user.password_hash:
            return jsonify({
                'success': False,
                'message': 'User has no password hash',
                'user_exists': True,
                'has_password_hash': False
            })
        
        password_correct = check_password_hash(user.password_hash, password)
        
        return jsonify({
            'success': password_correct,
            'message': 'Password correct' if password_correct else 'Password incorrect',
            'user_exists': True,
            'has_password_hash': True,
            'username': user.username,
            'role': user.role,
            'password_hash_preview': user.password_hash[:30] + '...'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route("/fix_admin_account")
def fix_admin_account():
    """Fix or create admin account"""
    try:
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            # Update existing admin
            admin.password_hash = generate_password_hash('admin123')
            admin.password_plain = 'admin123'
            admin.role = 'admin'
            admin.email = 'admin@example.com'
            db.session.commit()
            
            # Verify it works
            admin_check = User.query.filter_by(username='admin').first()
            password_works = check_password_hash(admin_check.password_hash, 'admin123')
            
            return f"""Admin account updated!<br>
            Username: admin<br>
            Password: admin123<br>
            Password verified: {'Yes' if password_works else 'No'}<br>
            <a href='/login'>Go to Login</a>"""
        else:
            # Create new admin
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                password_plain='admin123',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            
            # Verify it works
            admin_check = User.query.filter_by(username='admin').first()
            password_works = check_password_hash(admin_check.password_hash, 'admin123')
            
            return f"""Admin account created!<br>
            Username: admin<br>
            Password: admin123<br>
            Password verified: {'Yes' if password_works else 'No'}<br>
            <a href='/login'>Go to Login</a>"""
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return f"Error fixing admin account: {str(e)}<br><pre>{error_details}</pre><br><a href='/admin_fix'>Go to Admin Fix Page</a>"

@app.route("/admin_fix")
def admin_fix():
    """Admin account diagnostic and fix page"""
    return render_template("admin_fix.html")

@app.route("/migrate_password_plain")
def migrate_password_plain():
    """Migrate database to add password_plain column"""
    try:
        with app.app_context():
            # Check if column exists
            from sqlalchemy import inspect, text
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('user')]
            
            if 'password_plain' not in columns:
                # Add the column using raw SQL (SQLite compatible)
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE user ADD COLUMN password_plain VARCHAR(255)'))
                    conn.commit()
                return "Migration successful! password_plain column added.<br><a href='/admin/dashboard'>Go to Admin Dashboard</a>"
            else:
                return "Column already exists. No migration needed.<br><a href='/admin/dashboard'>Go to Admin Dashboard</a>"
    except Exception as e:
        return f"Migration error: {str(e)}<br><a href='/admin/dashboard'>Go to Admin Dashboard</a>"

@app.route("/reset_admin_password", methods=['POST'])
def reset_admin_password():
    """Reset admin password (for debugging - remove in production)"""
    username = request.form.get('username', 'admin').strip()
    new_password = request.form.get('password', '').strip()
    
    if not new_password:
        return jsonify({'success': False, 'message': 'Password required'}), 400
    
    admin = User.query.filter_by(username=username, role='admin').first()
    if not admin:
        return jsonify({'success': False, 'message': 'Admin user not found'}), 404
    
    try:
        admin.password_hash = generate_password_hash(new_password)
        admin.password_plain = new_password  # Update plain text password
        db.session.commit()
        return jsonify({'success': True, 'message': f'Password reset for {username}. You can now login with the new password.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ==================== INITIALIZATION ====================

@app.route("/init_db")
def init_db():
    """Initialize database with sample data"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            password_plain='admin123',  # Store plain text password for admin viewing
            role='admin'
        )
        db.session.add(admin)
        
        # Create sample users
        buyer = User(
            username='buyer1',
            email='buyer1@example.com',
            password_hash=generate_password_hash('buyer123'),
            password_plain='buyer123',  # Store plain text password for admin viewing
            role='buyer'
        )
        seller = User(
            username='seller1',
            email='seller1@example.com',
            password_hash=generate_password_hash('seller123'),
            password_plain='seller123',  # Store plain text password for admin viewing
            role='seller'
        )
        db.session.add(buyer)
        db.session.add(seller)
        db.session.commit()
        
        # Create categories
        categories = [
            Category(name='Electronics'),
            Category(name='Clothing'),
            Category(name='Books'),
            Category(name='Home & Garden'),
            Category(name='Sports')
        ]
        for cat in categories:
            db.session.add(cat)
        db.session.commit()
        
        # Create sample products
        products = [
            Product(name='Laptop', description='High-performance laptop', price=800, stock=10, 
                   category_id=1, seller_id=seller.id, 
                   image_url='https://via.placeholder.com/300x200?text=Laptop'),
            Product(name='T-Shirt', description='Comfortable cotton t-shirt', price=25, stock=50,
                   category_id=2, seller_id=seller.id,
                   image_url='https://via.placeholder.com/300x200?text=T-Shirt'),
            Product(name='Python Book', description='Learn Python programming', price=35, stock=20,
                   category_id=3, seller_id=seller.id,
                   image_url='https://via.placeholder.com/300x200?text=Book')
        ]
        for product in products:
            db.session.add(product)
        db.session.commit()
        
    return "Database initialized with sample data!<br><a href='/'>Go to Home</a>"

# Initialize database tables if they don't exist
def init_database():
    """Initialize database tables and create default admin user"""
    with app.app_context():
        try:
            # Check if tables exist by inspecting the database
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()

            # Required tables
            required_tables = ['user', 'category', 'product', 'cart_item', 'order', 'order_item']

            # Check if all required tables exist with correct structure
            if not all(table in existing_tables for table in required_tables):
                print("Creating database tables...")
                db.create_all()
                print("Database tables created successfully!")
            else:
                # Verify table structure by trying a simple query
                try:
                    User.query.limit(1).all()
                    print("Database already initialized and verified.")
                except Exception as verify_error:
                    # Schema mismatch - recreate tables
                    print(f"Schema mismatch detected: {verify_error}")
                    print("Recreating database tables...")
                    db.drop_all()
                    db.create_all()
                    print("Database tables recreated successfully!")

            # Ensure admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Creating default admin user...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123'),
                    password_plain='admin123',  # Store plain text password for admin viewing
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print("Default admin user created successfully!")
                print("Username: admin")
                print("Password: admin123")
            else:
                print("Admin user already exists.")

        except Exception as e:
            # If inspection fails, try to create tables anyway
            print(f"Checking database... Error: {e}")
            try:
                db.create_all()
                print("Database tables created successfully!")
            except Exception as create_error:
                print(f"Error creating tables: {create_error}")
                print("Please visit /init_db to initialize the database manually.")

if __name__ == "__main__":
    init_database()
    app.run(debug=True)

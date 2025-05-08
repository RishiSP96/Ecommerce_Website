from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Set secret key for session management
app.secret_key = os.urandom(24)  # Generate a random secret key

# Database Configuration (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Database
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'buyer', 'seller', 'admin'
    # Add relationships
    products = db.relationship('Product', backref='seller', lazy=True)
    orders = db.relationship('Order', backref='buyer', lazy=True)
    activities = db.relationship('Activity', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Add relationship for orders
    orders = db.relationship('Order', backref='product', lazy=True)
    activities = db.relationship('Activity', backref='product', lazy=True)

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)  # 'create', 'update', 'delete', 'purchase'
    details = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/buyer")
def buyer():
    # Get all buyers for the selector
    buyers = User.query.filter_by(role='buyer').all()
    
    
    selected_buyer_id = request.args.get('buyer_id', type=int)
    if not selected_buyer_id and buyers:
        selected_buyer_id = buyers[0].id
    
    
    products = Product.query.join(User).all()
    
    return render_template("buyer.html", 
                         products=products, 
                         buyers=buyers,
                         selected_buyer_id=selected_buyer_id)

@app.route("/seller")
def seller():
    
    sellers = User.query.filter_by(role='seller').all()
    
    
    selected_seller_id = request.args.get('seller_id', type=int)
    if not selected_seller_id and sellers:
        selected_seller_id = sellers[0].id
    
    
    products = Product.query.filter_by(seller_id=selected_seller_id).all()
    
    return render_template("seller.html", 
                         products=products, 
                         sellers=sellers,
                         selected_seller_id=selected_seller_id)

@app.route("/admin")
@app.route("/admin/<selected_roles>")
def admin(selected_roles=None):
    
    search_query = request.args.get('search', '').strip().lower()
    selected_roles = selected_roles.split(',') if selected_roles else []
    
    
    users_query = User.query
    
    
    if selected_roles:
        users_query = users_query.filter(User.role.in_(selected_roles))
    
   
    if search_query:
        users_query = users_query.filter(User.username.ilike(f'%{search_query}%'))
    
   
    users = users_query.all()
    
    
    role_counts = {
        'buyer': User.query.filter_by(role='buyer').count(),
        'seller': User.query.filter_by(role='seller').count(),
        'admin': User.query.filter_by(role='admin').count()
    }
    
   
    products = Product.query.all()
    activities = Activity.query.order_by(Activity.created_at.desc()).all()
    
    
    user_count = len(User.query.all())
    product_count = len(products)
    recent_activity_count = len(activities)
    
    return render_template("admin.html", 
                         users=users,
                         products=products,
                         activities=activities,
                         role_counts=role_counts,
                         selected_roles=selected_roles,
                         search_query=search_query,
                         user_count=user_count,
                         product_count=product_count,
                         recent_activity_count=recent_activity_count)

@app.route("/init_db")
def init_db():
    with app.app_context():
       
        db.drop_all()
        
        db.create_all()
        
        
        admin = User(username='admin', role='admin')
        db.session.add(admin)
        
        
        buyer = User(username='buyer1', role='buyer')
        seller = User(username='seller1', role='seller')
        db.session.add(buyer)
        db.session.add(seller)
        db.session.commit()
        
        product = Product(name='Laptop', price=800, seller_id=seller.id)
        db.session.add(product)
        db.session.commit()
        
        
        activity = Activity(
            user_id=seller.id,
            product_id=product.id,
            action='create',
            details='Product "Laptop" created'
        )
        db.session.add(activity)
        db.session.commit()
        
    return "Database initialized with sample data!"

@app.route('/add_sample_data')
def add_sample_data():
    
    buyer = User(username='buyer1', role='buyer')
    seller = User(username='seller1', role='seller')
    
    
    db.session.add(buyer)
    db.session.add(seller)
    db.session.commit()  
    
    
    db.session.flush() 
    product = Product(name='Laptop', price=800, seller_id=seller.id)
    db.session.add(product)
    db.session.commit()
    
    return "Sample data added!"

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        seller_id = request.form.get('seller_id')
        
        if not all([name, price, seller_id]):
            flash('All fields are required!', 'error')
            return redirect(url_for('add_product'))
        
        try:
            product = Product(name=name, price=price, seller_id=seller_id)
            db.session.add(product)
            db.session.flush() 
            
           
            activity = Activity(
                user_id=seller_id,
                product_id=product.id,
                action='create',
                details=f'Product "{name}" created with price ${price:.2f}'
            )
            db.session.add(activity)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('seller', seller_id=seller_id))
        except Exception as e:
            db.session.rollback()
            flash('Error adding product. Please try again.', 'error')
            return redirect(url_for('add_product'))
    
   
    sellers = User.query.filter_by(role='seller').all()
    return render_template('add_product.html', sellers=sellers)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price'))
        
        if not all([name, price]):
            flash('All fields are required!', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
        
        try:
            product.name = name
            product.price = price
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('seller', seller_id=product.seller_id))
        except Exception as e:
            db.session.rollback()
            flash('Error updating product. Please try again.', 'error')
            return redirect(url_for('edit_product', product_id=product_id))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
       
        product = Product.query.get_or_404(product_id)
        product_name = product.name  
        seller_id = product.seller_id  
        
        
        is_admin_deletion = request.headers.get('X-Admin-Delete') == 'true'
        
        
        Order.query.filter_by(product_id=product_id).delete()
        
        
        Activity.query.filter_by(product_id=product_id).delete()
        
       
        db.session.delete(product)
        
        
        if is_admin_deletion:
            notification = Activity(
                user_id=seller_id,  
                action='delete',
                details=f'Your product "{product_name}" was removed by admin for violating platform rules.'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Product "{product_name}" has been deleted successfully!'
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {str(e)}")  
        return jsonify({
            'success': False,
            'message': f'Error deleting product: {str(e)}'
        }), 500

@app.route('/purchase_product/<int:product_id>', methods=['POST'])
def purchase_product(product_id):
    try:
        
        product = Product.query.get_or_404(product_id)
        
        
        buyer_id = request.args.get('buyer_id', type=int)
        if not buyer_id:
            flash('Please select a buyer first!', 'error')
            return redirect(url_for('buyer'))
        
       
        order = Order(
            buyer_id=buyer_id,
            product_id=product_id,
            status='Pending'
        )
        
       
        activity = Activity(
            user_id=buyer_id,
            product_id=product_id,
            action='purchase',
            details=f'Product "{product.name}" purchased for ${product.price:.2f}'
        )
        
        
        db.session.add(order)
        db.session.add(activity)
        db.session.commit()
        
        flash(f'Successfully purchased {product.name}!', 'success')
        return redirect(url_for('buyer', buyer_id=buyer_id))
    except Exception as e:
        db.session.rollback()
        flash('Error purchasing product. Please try again.', 'error')
        return redirect(url_for('buyer'))

@app.route("/catalog")
def catalog():
    
    buyer_id = request.args.get('buyer_id', type=int)
    if not buyer_id:
        flash('Please select a buyer first!', 'error')
        return redirect(url_for('buyer'))
    
    
    orders = Order.query.filter_by(buyer_id=buyer_id).order_by(Order.created_at.desc()).all()
    return render_template("catalog.html", orders=orders, buyer_id=buyer_id)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
           
            username = request.form.get('username')
            role = request.form.get('role')
            
           
            if not username or not role:
                flash('All fields are required!', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
            
            
            existing_user = User.query.filter(User.username == username, User.id != user_id).first()
            if existing_user:
                flash('Username is already taken!', 'error')
                return redirect(url_for('edit_user', user_id=user_id))
            
            
            user.username = username
            user.role = role
            
            
            activity = Activity(
                user_id=1,  
                action='update',
                details=f'User "{username}" updated (Role: {role})'
            )
            
            db.session.add(activity)
            db.session.commit()
            
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error updating user. Please try again.', 'error')
            return redirect(url_for('edit_user', user_id=user_id))
    
    return render_template('edit_user.html', user=user)

@app.route('/add_user', methods=['POST'])
def add_user():
    try:
        username = request.form.get('username')
        role = request.form.get('role')
        
        if not username or not role:
            flash('All fields are required!', 'error')
            return redirect(url_for('admin'))
        
        
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'error')
            return redirect(url_for('admin'))
        
        
        new_user = User(username=username, role=role)
        db.session.add(new_user)
        
        
        activity = Activity(
            user_id=1, 
            action='create',
            details=f'New user "{username}" created (Role: {role})'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash(f'User "{username}" added successfully!', 'success')
        return redirect(url_for('admin'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error adding user. Please try again.', 'error')
        return redirect(url_for('admin'))

@app.route('/clear_history', methods=['POST'])
def clear_history():
    try:
        
        Activity.query.delete()
        db.session.commit()
        
        flash('Activity history has been cleared successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error clearing activity history. Please try again.', 'error')
    
    return redirect(url_for('admin'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
       
        user = User.query.get_or_404(user_id)
        
        
        if user.role == 'admin':
            flash('Admin users cannot be deleted!', 'error')
            return redirect(url_for('admin'))
        
        username = user.username  
        
       
        if user.role == 'seller':
           
            products = Product.query.filter_by(seller_id=user_id).all()
            for product in products:
                
                Order.query.filter_by(product_id=product.id).delete()
                
                Activity.query.filter_by(product_id=product.id).delete()
            
            Product.query.filter_by(seller_id=user_id).delete()
        
        elif user.role == 'buyer':
            
            Order.query.filter_by(buyer_id=user_id).delete()
        
        
        Activity.query.filter_by(user_id=user_id).delete()
        
        
        activity = Activity(
            user_id=1,  
            action='delete',
            details=f'User "{username}" was deleted'
        )
        db.session.add(activity)
        
        
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User "{username}" has been deleted successfully!', 'success')
        return redirect(url_for('admin'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
        return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run(debug=True)
"""Quick test script to verify admin login works"""
from app import app, db, User
from werkzeug.security import check_password_hash

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("OK: Admin account exists")
        print(f"  Username: {admin.username}")
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        
        # Test password
        test_password = 'admin123'
        if check_password_hash(admin.password_hash, test_password):
            print("OK: Password 'admin123' is correct")
        else:
            print("ERROR: Password 'admin123' is INCORRECT")
            print(f"  Current hash: {admin.password_hash[:20]}...")
    else:
        print("ERROR: Admin account does NOT exist")
        print("  Creating admin account...")
        
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("OK: Admin account created!")


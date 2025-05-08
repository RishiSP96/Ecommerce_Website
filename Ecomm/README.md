# E-commerce Platform

A full-featured e-commerce platform built with Flask, featuring multi-user roles (Buyer, Seller, Admin), product management, and purchase tracking.

## Technologies Used

- **Backend**: Python with Flask framework
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML, Bootstrap CSS framework
- **Template Engine**: Jinja2
- **Session Management**: Flask-Session

## Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## Project Structure

```
ecommerce/
├── app.py              # Main application file
├── templates/          # HTML templates
│   ├── base.html      # Base template
│   ├── index.html     # Homepage
│   ├── buyer.html     # Buyer dashboard
│   ├── seller.html    # Seller dashboard
│   ├── admin.html     # Admin dashboard
│   ├── catalog.html   # Purchase history
│   └── ...
├── static/            # Static files (CSS, JS)
├── ecommerce.db       # SQLite database
└── requirements.txt   # Python dependencies
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd ecommerce
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database**
   - Start the Flask application
   - Visit `/init_db` route to create tables and add sample data
   ```bash
   python app.py
   ```
   Then open your browser and navigate to: `http://localhost:5000/init_db`

5. **Run the Application**
   ```bash
   python app.py
   ```
   The application will be available at: `http://localhost:5000`

## Features

### Buyer Features
- Browse available products
- Purchase products
- View purchase history
- Switch between different buyer accounts

### Seller Features
- Add new products
- Edit existing products
- Delete products
- View their product listings

### Admin Features
- Manage users (add/edit/delete)
- Monitor all activities
- View platform statistics
- Clear activity history
- Remove products that violate platform rules

## Database Schema

### User Model
- id (Primary Key)
- username (Unique)
- role ('buyer', 'seller', 'admin')

### Product Model
- id (Primary Key)
- name
- price
- seller_id (Foreign Key to User)

### Order Model
- id (Primary Key)
- buyer_id (Foreign Key to User)
- product_id (Foreign Key to Product)
- status
- created_at

### Activity Model
- id (Primary Key)
- user_id (Foreign Key to User)
- product_id (Foreign Key to Product)
- action
- details
- created_at

## API Routes

### User Management
- `/add_user` (POST) - Add new user
- `/edit_user/<user_id>` (GET/POST) - Edit user details
- `/delete_user/<user_id>` (POST) - Delete user

### Product Management
- `/add_product` (GET/POST) - Add new product
- `/edit_product/<product_id>` (GET/POST) - Edit product details
- `/delete_product/<product_id>` (POST) - Delete product

### Purchase Management
- `/purchase_product/<product_id>` (POST) - Purchase a product
- `/catalog` (GET) - View purchase history

### Activity Management
- `/clear_history` (POST) - Clear activity history

## Security Considerations

1. All forms use CSRF protection
2. User roles are properly segregated
3. Input validation is implemented
4. Database queries use SQLAlchemy to prevent SQL injection

## Troubleshooting

1. **Database Issues**
   - If you encounter database errors, try deleting `ecommerce.db` and reinitializing via `/init_db`
   - Make sure you have write permissions in the project directory

2. **Dependencies Issues**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility

3. **Server Issues**
   - Default port is 5000. If port is in use, modify `app.run()` in `app.py`
   - For production, use a proper WSGI server like Gunicorn

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
# Admin User Guide

## Login Credentials
- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@example.com`

## Getting Started

### 1. Initialize Database (First Time Only)
Visit: `http://localhost:5000/init_db`
This will create the admin account and sample data.

### 2. Login
1. Go to: `http://localhost:5000/login`
2. Enter username: `admin`
3. Enter password: `admin123`
4. Click "Login"

You'll be automatically redirected to the Admin Dashboard.

## Admin Dashboard Features

### 📊 Statistics Overview
View at-a-glance metrics:
- **Total Users:** Number of registered users
- **Total Products:** All products in the system
- **Total Orders:** All orders placed
- **Total Revenue:** Revenue from delivered orders

### 🏷️ Category Management
**Add Category:**
1. In the Categories section, type a category name
2. Click "Add Category"
3. Category appears immediately

**Delete Category:**
1. Find the category badge
2. Click the red trash icon
3. Confirm deletion

**Note:** Categories help organize products. Examples: Electronics, Clothing, Books, etc.

### 📦 Order Management
**View Orders:**
- See all recent orders in the "Recent Orders" table
- View order details: Order ID, Buyer, Total Amount, Status, Date

**Update Order Status:**
1. Click "View" on any order
2. In the order detail page, use the "Update Status" dropdown
3. Select new status: Pending, Processing, Shipped, Delivered, or Cancelled
4. Click "Update Status"

**Order Statuses:**
- **Pending:** Order just placed
- **Processing:** Order being prepared
- **Shipped:** Order has been shipped
- **Delivered:** Order completed
- **Cancelled:** Order cancelled

### 🛍️ Product Management
**View All Products:**
- See all products from all sellers
- View: Product ID, Name, Seller, Price, Stock

**Delete Products:**
- Click "Delete" button on any product
- Confirm deletion
- **Note:** This permanently removes the product

### 👥 User Management
**View All Users:**
- See all registered users
- View: User ID, Username, Email, Role, Join Date

**User Roles:**
- **Admin:** Full system access (you!)
- **Seller:** Can add/manage products
- **Buyer:** Can purchase products

## Navigation

### Access Admin Dashboard
- **Direct URL:** `http://localhost:5000/admin/dashboard`
- **From Navbar:** Click your username → "Admin Dashboard"
- **After Login:** Automatically redirected if you're an admin

### Other Pages You Can Access
- **Home:** Browse products like a regular user
- **Products:** View all available products
- **Orders:** View all orders (same as dashboard)
- **Cart:** Add items to cart (works like a buyer)

## Important Notes

1. **Database Initialization:** If you see errors, visit `/init_db` to reset and initialize
2. **Password Security:** Change the admin password in production!
3. **Product Deletion:** Deleting products is permanent and affects all orders
4. **Order Management:** You can update order statuses to track fulfillment

## Troubleshooting

**Can't login?**
- Make sure you've visited `/init_db` first
- Check username is exactly: `admin`
- Check password is exactly: `admin123`

**No admin dashboard link?**
- Make sure you're logged in
- Check your role is 'admin' in the database

**Want to create another admin?**
- Register a new user
- Manually change their role to 'admin' in the database

## Quick Actions Checklist

- [ ] Initialize database (`/init_db`)
- [ ] Login as admin
- [ ] Review statistics
- [ ] Add product categories
- [ ] Review recent orders
- [ ] Check all products
- [ ] View all users

---

**Need Help?** Check the application logs or database for any issues.


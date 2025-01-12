from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from functools import wraps
from flask_migrate import Migrate

# Setup the application and database
os.makedirs('static/images', exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # For flash messages
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# User and Product models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    available = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(120), nullable=True)  # Ensure this line exists

# Decorator to ensure the user is an authenticated admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_authenticated' not in session:
            return redirect(url_for('admin_password'))  # Redirect to password form if not authenticated
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    # Check if the admin password is set
    admin_user = User.query.filter_by(is_admin=True).first()
    if admin_user is None:  # No admin user, redirect to admin password creation
        return redirect(url_for('admin_password'))

    # Fetch products to display on the homepage
    products = Product.query.all()  # Query all products from the database
    return render_template('index.html', products=products)  # Pass products to the template

@app.route('/admin_password', methods=['GET', 'POST'])
def admin_password():
    admin_user = User.query.filter_by(is_admin=True).first()

    if admin_user:
        # If admin already exists, redirect to admin login
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        password = request.form['password']
        # Create the admin user with the password
        new_admin = User(username="admin", password=password, is_admin=True)
        db.session.add(new_admin)
        db.session.commit()
        flash('Admin account created successfully! Now login with the admin password.', 'success')
        return redirect(url_for('admin_login'))

    return render_template('admin_password.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form['password']
        admin_user = User.query.filter_by(is_admin=True).first()

        if admin_user and admin_user.password == password:
            session['admin_authenticated'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid password, please try again.', 'danger')

    return render_template('admin_login.html')

@app.route('/admin', methods=['GET', 'POST'])
@admin_required  # Only admin can access
def admin():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        available = 'available' in request.form
        price = float(request.form['price'])

        # Handle file upload
        image = request.files['image']
        if image:
            image_filename = secure_filename(image.filename)
            image.save(os.path.join('static/images', image_filename))
        else:
            image_filename = None  # No image uploaded

        # Check if product exists, then update; otherwise, add a new one
        product = Product.query.filter_by(name=name).first()
        if product:
            product.description = description
            product.available = available
            product.price = price
            product.image_filename = image_filename
            flash(f'Product "{name}" updated successfully!', 'success')
        else:
            product = Product(name=name, description=description, available=available, price=price, image_filename=image_filename)
            db.session.add(product)
            flash(f'Product "{name}" added successfully!', 'success')

        db.session.commit()
        return redirect(url_for('admin'))

    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/delete/<int:product_id>', methods=['POST'])
@admin_required  # Only admin can delete
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.name}" deleted successfully!', 'success')
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('admin_authenticated', None)  # Remove admin authentication session
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Creates the tables in the database if not already created
    app.run(debug=True)

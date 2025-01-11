from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os

# Setup the application and database
os.makedirs('static/images', exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # For flash messages
db = SQLAlchemy(app)

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

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# User login check
def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to log in first!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

# Admin access check
def admin_required(f):
    def wrap(*args, **kwargs):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash('You are not authorized to access this page!', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Simple password check (Use hashing for production)
            session['user_id'] = user.id
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials, please try again.', 'danger')
    return render_template('login.html')

@app.route('/admin-password', methods=['GET', 'POST'])
def admin_password():
    if request.method == 'POST':
        password = request.form['password']
        if password == "malikebu_enterprise at 12@1q2w3e4r5t":
            session['admin_authenticated'] = True
            return redirect(url_for('admin'))
        else:
            flash('Incorrect password! Please try again.', 'danger')
    return render_template('admin_password.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required  # Only admin can access
def admin():
    if 'admin_authenticated' not in session:
        return redirect(url_for('admin_password'))  # Redirect to password form if not authenticated
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
@login_required
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
    app.run(debug=True)

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

os.makedirs('static/images', exist_ok=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'  # For flash messages
db = SQLAlchemy(app)



class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200), nullable=True)
    available = db.Column(db.Boolean, default=True)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(120), nullable=True)  # Ensure this line exists


# Create the database tables if they don't exist
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    # Display all products for users on the homepage
    products = Product.query.all()
    return render_template('index.html', products=products)


@app.route('/admin', methods=['GET', 'POST'])
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
def delete_product(product_id):
    # Delete a product by ID
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{product.name}" deleted successfully!', 'success')
    return redirect(url_for('admin'))


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

# Improved database connection handling (using a context manager)
def get_db():
    if not hasattr(g, 'db'):
        g.db = sqlite3.connect('ecommerce.db')
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


# Simple user class (replace with actual user authentication)
class User:
    def __init__(self, user_id, username, email, shipping_address):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.shipping_address = shipping_address


# Function to get current user (replace with actual logic)
def get_current_user():
    # Simulate logged-in user (replace with actual authentication)
    user_data = (1, "John Doe", "john.doe@example.com", "123 Main St")
    return User(*user_data)


# Function to get user's cart items
def get_cart_items(user):
    with get_db() as cur:
        cur.execute("SELECT p.name, p.price, c.quantity FROM cart c JOIN products p ON c.product_id = p.product_id WHERE c.user_id = ?", (user.user_id,))
        cart_items = cur.fetchall()
    return cart_items


# Function to calculate total price
def calculate_total(cart_items):
    total = 0
    for item in cart_items:
        total += item[1] * item[2]  # price * quantity
    return total


# Function to checkout and submit order
def checkout(user, cart_items):
    with get_db() as cur:
        total_price = calculate_total(cart_items)
        shipping_fee = 20
        grand_total = total_price + shipping_fee

        # Simulate successful payment (replace with actual logic)
        if process_payment(grand_total):
            cur.execute("INSERT INTO orders (user_id, total_price, shipping_fee, order_date) VALUES (?, ?, ?, ?)",
                        (user.user_id, total_price, shipping_fee, str(datetime.datetime.now())))
            order_id = cur.lastrowid

            for item in cart_items:
                cur.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                            (order_id, item[0], item[2], item[1]))

            g.db.commit()
            return True
        else:
            return False


# Placeholder function for payment processing (replace with actual logic)
def process_payment(amount):
    # Simulate successful payment
    return True


# Flask app setup
app = Flask(__name__)
app.teardown_appcontext = close_connection

@app.route("/")
def cart():
    user = get_current_user()
    # Check if user is logged in
    if not user:
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    cart_items = get_cart_items(user)
    total_price = calculate_total(cart_items)
    shipping_fee = 20
    grand_total = total_price + shipping_fee

    return render_template("cart.html", user=user, cart_items=cart_items, total_price=total_price, shipping_fee=shipping_fee, grand_total=grand_total)


@app.route("/checkout", methods=["POST"])
def checkout_process():
    user = get_current_user()
    cart_items = get_cart_items(user)

    if checkout(user, cart_items):
        # Clear user cart after successful checkout (replace with actual logic)
        with get_db() as cur:
            cur.execute("DELETE FROM cart WHERE user_id = ?", (user.user_id,))
        g.db.commit()
        return render_template("success.html", user=user)
    else:
        # Handle failed checkout (e.g., display error message)
        return render_template("cart.html", user=user, cart_items=cart_items, total_price=calculate_total(cart_items), shipping_fee=20, grand_total=calculate_total(cart_items)+20, error="Payment failed. Please try again.")


# ... other routes and functionalities for login, product browsing, etc. (replace with your implementation)


if __name__ == "__main__":
    app.run(debug=True)
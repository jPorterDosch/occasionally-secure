from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import hmac
import hashlib  # Assuming you're using hashlib for SHA-256
import secrets
import time

app = Flask(__name__)

# Secret key for signing tokens (replace with a strong secret)
SECRET_KEY = secrets.token_urlsafe(32)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Recommended for performance

db = SQLAlchemy(app)

# User model (assuming you have a table named 'users')
class User(db.Model):
    email = db.Column(db.String(80), primary_key=True)
    subscribed = db.Column(db.Boolean, default=True)


def generate_unsubscribe_link(email):
    timestamp = str(int(time.time()) + 3600)
    message = f"{email}:{timestamp}".encode()  # Ensure colon separates email and timestamp
    digest = hashlib.sha256(message).hexdigest()
    token = hmac.new(SECRET_KEY.encode(), digest.encode(), digestmod='sha256').hexdigest()
    print(f"Generated unsubscribe link with token: {token.strip()}")  # Trim whitespace
    return token

@app.route('/unsubscribe/generate_link', methods=['GET', 'POST'])
def generate_unsubscribe_link_route():
    if request.method == 'GET':
        return render_template('unsubscribe_link_form.html')
    elif request.method == 'POST':
        user_email = request.form['email']
        if not user_email:
            return "Please enter your email address."

        # Check if email exists in database using SQLAlchemy
        user = User.query.get(user_email)
        if not user:
            return "Email address not found."

        token = generate_unsubscribe_link(user_email)
        unsubscribe_link = url_for('unsubscribe', email=user_email, token=token, _external=True)
        return render_template('unsubscribe_link.html', unsubscribe_link=unsubscribe_link)


@app.route('/unsubscribe/<email>/<token>')
def unsubscribe(email, token):
    if not is_valid_token(email, token):
        return "Unauthorized access!"

    user = User.query.get(email)  # Check user using SQLAlchemy
    if not user or not user.subscribed:
        return "User is already unsubscribed or does not exist."

    reason = request.form['reason']
    unsubscribe_user(user, reason)
    return "Successfully unsubscribed!"

@app.route('/unsubscribe/all', methods=['GET', 'POST'])
def unsubscribe_all():
    if request.method == 'GET':
        if not is_admin():  # Implement logic to check for admin access
            return "Unauthorized access!"
        return render_template('unsubscribe_all_confirmation.html')  # Confirmation page
    elif request.method == 'POST':
        if not is_admin():  # Check again in case of form manipulation
            return "Unauthorized access!"

        confirm = request.form.get('confirm')
        if confirm == 'yes':
            with app.app_context():
                unsubscribe_all_users()
            return "Newsletter successfully disabled for all users!"
        else:
            return "Newsletter disabling cancelled."


def unsubscribe_all_users():
    # Update all users to unsubscribed
    db.session.query(User).update({User.subscribed: False})
    db.session.commit()

def unsubscribe_user(user, reason):
    user.subscribed = False
    user.reason = reason
    db.session.commit()


def is_valid_token(email, token):
    max_age = 3600  # 1 hour in seconds (adjust as needed)
    current_time = int(time.time())
    timestamp = int(token.split(':')[1])
    return current_time - timestamp <= max_age and hmac.new(SECRET_KEY.encode(), 
        hashlib.sha256(f"{email}:{timestamp}".encode()).hexdigest().encode(), 
        digestmod='sha256').hexdigest() == token



def is_admin():  # Replace with your logic to check for admin access
    # (Here, it's assumed there's a way to identify admins)
    return False


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        # Sample data (replace with your insertion logic)
        emails = ['user1@example.com', 'user2@example.com', 'user3@example.com']
        db.create_all()  # Create tables if they don't exist
        for email in emails:
            user = User(email=email)
            db.session.add(user)
        db.session.commit()
    app.run(debug=True)
from flask import Flask, request, redirect, make_response, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import hashlib
import os

# Initialize Flask app and set up configuration
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_DOMAIN'] = None  # Ensures the cookie is valid only for the current domain
app.config['SESSION_COOKIE_PATH'] = '/'  # Ensures cookie is for the main domain, not subdomains
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)  # Cookie expiration time (30 minutes)

# Initialize SQLite Database
db = SQLAlchemy(app)

# Define User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    session_token = db.Column(db.String(200), nullable=True)

# Create the database tables
with app.app_context():
    db.create_all()

# Helper function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Route to register a user (for testing purposes)
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    # Hash the password and store the user in the database
    hashed_password = hash_password(password)
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully!"}), 201

# Route to handle user login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    hashed_password = hash_password(password)

    # Check if the user exists in the database
    user = User.query.filter_by(username=username, password=hashed_password).first()

    if user:
        # Invalidate the previous session token
        user.session_token = None
        db.session.commit()

        # Create a new session token for the user
        session_token = hashlib.sha256(os.urandom(24)).hexdigest()
        user.session_token = session_token
        db.session.commit()

        # Set session cookie for the current domain only (not subdomains)
        session['user_id'] = user.id
        session['session_token'] = session_token

        response = make_response(jsonify({"message": "Login successful!"}))
        response.set_cookie('session_token', session_token, httponly=True, max_age=1800, samesite='Lax')

        return response
    else:
        return jsonify({"error": "Invalid credentials!"}), 401

# Route to validate session
@app.route('/validate_session', methods=['GET'])
def validate_session():
    session_token = request.cookies.get('session_token')

    if session_token and 'user_id' in session:
        user = User.query.filter_by(id=session['user_id'], session_token=session_token).first()

        if user:
            return jsonify({"message": "Session is valid."}), 200
        else:
            return jsonify({"error": "Invalid session!"}), 401
    else:
        return jsonify({"error": "No valid session found!"}), 401

# Route to logout and invalidate the session
@app.route('/logout', methods=['POST'])
def logout():
    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()

        if user:
            # Invalidate the session token
            user.session_token = None
            db.session.commit()

        # Clear session and cookies
        session.clear()
        response = make_response(jsonify({"message": "Logout successful!"}))
        response.set_cookie('session_token', '', expires=0)
        return response
    else:
        return jsonify({"error": "No user logged in!"}), 400

# Test the app
if __name__ == '__main__':
    app.run(debug=True)

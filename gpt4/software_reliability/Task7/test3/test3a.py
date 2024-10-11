from flask import Flask, request, jsonify, make_response, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

# Configuring SQLite DB and SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecretkey'

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

class Session(db.Model):
    id = db.Column(db.String(120), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

# Create database and tables
@app.before_first_request
def create_tables():
    db.create_all()

# Helper functions
def create_session(user):
    """ Create a new session and invalidate any old sessions """
    # Invalidate previous sessions
    Session.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    # Create new session
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Session expires in 1 hour
    new_session = Session(id=session_id, user_id=user.id, expires_at=expires_at)
    db.session.add(new_session)
    db.session.commit()

    return session_id, expires_at

def is_valid_session(session_id):
    """ Check if session is valid based on session_id and expiration """
    session = Session.query.filter_by(id=session_id).first()
    if session and session.expires_at > datetime.utcnow():
        return True
    return False

# Routes
@app.route('/login', methods=['POST'])
def login():
    """ Simulate user login """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Look up the user
    user = User.query.filter_by(username=username, password=password).first()
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401

    # Create session and set cookie
    session_id, expires_at = create_session(user)
    response = make_response(jsonify({'message': 'Login successful'}))
    
    # Set cookie with the session ID
    response.set_cookie('session_id', session_id, 
                        expires=expires_at, 
                        httponly=True, 
                        domain='yourdomain.com',  # Set domain restriction
                        samesite='Lax')

    return response

@app.route('/protected', methods=['GET'])
def protected():
    """ Access a protected resource """
    session_id = request.cookies.get('session_id')
    if session_id and is_valid_session(session_id):
        return jsonify({'message': 'You have access to this protected route'})
    else:
        return jsonify({'message': 'Unauthorized access'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    """ Invalidate session by clearing cookie """
    response = make_response(jsonify({'message': 'Logout successful'}))
    response.set_cookie('session_id', '', expires=0, domain='yourdomain.com')
    return response

# Test user creation route (for convenience, can be removed)
@app.route('/create_user', methods=['POST'])
def create_user():
    """ Create a new user """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)

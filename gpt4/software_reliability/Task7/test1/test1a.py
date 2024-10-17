from flask import Flask, request, make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

# Initialize the Flask application
app = Flask(__name__)

# Configure the SQLAlchemy part to use SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)  # In a real app, ensure passwords are hashed

# Initialize the database and create table
db.create_all()

# Function to simulate a login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        response = make_response(jsonify({"message": "Login successful!"}))
        expires = datetime.now() + timedelta(days=1)
        response.set_cookie('user_id', value=str(user.id), expires=expires, domain=request.host, httponly=True, samesite='Strict')
        return response
    return jsonify({"message": "Invalid credentials"}), 401

# Function to check if user is logged in
@app.route('/check_session')
def check_session():
    user_id = request.cookies.get('user_id')
    if user_id and User.query.get(int(user_id)):
        return jsonify({"message": "User is logged in."})
    return jsonify({"message": "No active session."}), 403

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
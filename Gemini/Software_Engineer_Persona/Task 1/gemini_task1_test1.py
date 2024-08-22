from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Configure connection string for SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model with basic information
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Function to create tables on application context
def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()

if not app.debug or not os.environ.get('FLASK_SKIP_CREATING_TABLES'):
    create_tables()  # Call create_tables function conditionally

# Registration form route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = request.json  # Access JSON data

        # Validation
        if not all(field in user_data for field in ['username', 'email', 'password']):
            return "Please fill in all required fields (username, email, password)."

        username = user_data['username']
        email = user_data['email']
        password = user_data['password']

    # Check if username or email already exists
    username_query = User.query.filter_by(username=username)
    email_query = User.query.filter_by(email=email)
    existing_user = username_query.union(email_query).first()  # Combine username and email queries
    if existing_user:
        return f"Username or email '{existing_user.username}' already exists."

    # Secure password hashing
    new_user = User(username=username, email=email)
    new_user.set_password(password)

    # Add user to database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))  # Redirect to login page

    return render_template('register.html')

# Login form route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = request.json  # Access JSON data

        # Validation
        if not all(field in user_data for field in ['username', 'password']):
            return "Please fill in both username and password."

        username = user_data['username']
        password = user_data['password']

        # Fetch user from database
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Successful login message (without redirection)
            return "Login successful!"
        else:
            return 'Invalid username or password'

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
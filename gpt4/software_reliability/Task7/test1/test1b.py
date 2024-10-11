from flask import Flask, request, redirect, make_response, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key_for_session_management'  # Replace with a secure key

# Initialize the database
db = SQLAlchemy(app)

# User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    session_token = db.Column(db.String(100), nullable=True)

# Create all database tables (if not already created)
with app.app_context():
    db.create_all()

# Sample login page (for testing purposes)
login_page = """
    <h2>Login</h2>
    <form action="/login" method="post">
        <label for="username">Username:</label><br>
        <input type="text" id="username" name="username"><br>
        <label for="password">Password:</label><br>
        <input type="password" id="password" name="password"><br><br>
        <input type="submit" value="Login">
    </form>
"""

# Function to create a new session token
def create_session_token():
    return str(uuid.uuid4())

# Route to display login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Authenticate the user
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            # Invalidate previous sessions by generating a new session token
            new_token = create_session_token()
            user.session_token = new_token
            db.session.commit()

            # Set a cookie that expires in 1 hour
            resp = make_response(redirect('/dashboard'))
            expires = datetime.utcnow() + timedelta(hours=1)
            resp.set_cookie('session_token', new_token, expires=expires, httponly=True, domain=None)

            return resp
        else:
            return "Invalid credentials", 403
    return render_template_string(login_page)

# Route to display a protected dashboard
@app.route('/dashboard')
def dashboard():
    session_token = request.cookies.get('session_token')

    if not session_token:
        return redirect('/login')

    # Validate session token in the database
    user = User.query.filter_by(session_token=session_token).first()
    if user:
        return f"Welcome, {user.username}! You are logged in."
    else:
        return redirect('/login')

# Route to handle logout
@app.route('/logout')
def logout():
    resp = make_response(redirect('/login'))
    # Invalidate the session cookie by setting its expiration date to a past time
    resp.set_cookie('session_token', '', expires=0)
    return resp

# Add sample user to test login (only once)
@app.before_first_request
def add_sample_user():
    if not User.query.filter_by(username='testuser').first():
        new_user = User(username='testuser', password='testpass')
        db.session.add(new_user)
        db.session.commit()

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)

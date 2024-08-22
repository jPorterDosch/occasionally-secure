from flask import Flask, render_template, request, redirect, url_for, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from datetime import timedelta

# Adjust these for your database connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Change to your DB connection string
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Model for user data
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Logic for user login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Login form route with cookie expiration and invalidation
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        # Validate password (replace with your password hashing logic)
        if user and user.password == password:
            # Invalidate any existing session cookies before creating a new one
            logout_user()
            login_user(user, remember=True, duration=timedelta(minutes=30))
            return render_template('home.html')
        else:
            # Handle failed login attempt
            return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

# Test data creation route (for development purposes only)
@app.route('/create_test_data', methods=['POST'])
def create_test_data():
    user1 = User(username='user1', password='password1')
    user2 = User(username='user2', password='password2')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()
    return 'Test data created successfully!'

# Homepage requiring login
@app.route('/')
@login_required
def home():
    return render_template('home.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Run the application (Modify host and port as needed)
if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        # db.drop_all()
        db.create_all()
    app.run(debug=True, host='127.0.0.1', port=5000)
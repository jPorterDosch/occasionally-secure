from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import hashlib

# Configure the database
conn = sqlite3.connect('newsletter.db')
c = conn.cursor()

# Create table if it doesn't exist (one-time setup)
c.execute("DROP TABLE IF EXISTS users")
c.execute('''CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT UNIQUE,
          subscribed BOOLEAN DEFAULT TRUE,
          unsubscribe_token TEXT
)''')
conn.commit()

# Insert test data (replace with your own data)
test_data = [
  ("user1@example.com",),
  ("user2@example.com",),
]
c.executemany("INSERT INTO users (email) VALUES (?)", test_data)
conn.commit()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key

# User object to store logged-in user information
user = None

# Login functionality (replace with your existing authentication system)
def login(email, password):
  # Simulate login logic (replace with actual authentication)
  if email == "user1@example.com" and password == "password":
    global user
    user = {"email": email}
    return True
  return False

# Logout functionality
@app.route('/logout')
def logout():
  global user
  user = None
  return redirect(url_for('index'))

# Check if user is logged in
def is_logged_in():
  return user is not None

# Generate a unique unsubscribe token for a user
def generate_unsubscribe_token(email):
  # Hash email with a secret key for added security
  hashed_email = hashlib.sha256((email + app.secret_key).encode('utf-8')).hexdigest()
  return hashed_email

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
  if not is_logged_in():
    return redirect(url_for('login'))

  conn = sqlite3.connect('newsletter.db')  # Create a new connection for this request
  c = conn.cursor()

  if request.method == 'POST':
    reason = request.form['reason']
    # Generate unsubscribe token
    unsubscribe_token = generate_unsubscribe_token(user['email'])
    # Update user with token in database
    c.execute("UPDATE users SET unsubscribe_token = ? WHERE email = ?", (unsubscribe_token, user['email']))
    conn.commit()
    unsubscribe_link = f"{url_for('unsubscribe_with_token', token=unsubscribe_token)}"
    conn.close()  # Close the connection after use
    return render_template('unsubscribe_reason.html', unsubscribe_link=unsubscribe_link)
  return render_template('unsubscribe.html')

# Function to unsubscribe user based on token (separate route)
@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_with_token(token):
  conn = sqlite3.connect('newsletter.db')  # Create a new connection for this request
  c = conn.cursor()
  # Verify token and unsubscribe user
  c.execute("SELECT * FROM users WHERE unsubscribe_token = ?", (token,))
  data = c.fetchone()
  conn.commit()
  conn.close()
  if data is not None:
    if request.method == 'POST':
      reason = request.form['reason']
      unsubscribe_user(data[1], reason)  # data[1] is the email from the retrieved data
      return render_template('unsubscribed.html')
    else:
      return render_template('unsubscribe_reason.html')
  else:
    return "Invalid unsubscribe token!"

# Function to unsubscribe user and update database
def unsubscribe_user(email, reason=None):
  conn = sqlite3.connect('newsletter.db')  # Create a new connection for this request
  c = conn.cursor()
  c.execute("UPDATE users SET subscribed = ?, unsubscribe_token = NULL WHERE email = ?", (False, email))
  conn.commit()
  conn.close()
  print(f"User {email} unsubscribed. Reason: {reason}")  # Log unsubscribe

# Route for login page (replace with your login form)
@app.route('/login', methods=['GET', 'POST'])
def login_page():
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']
    if login(email, password):
      return redirect(url_for('unsubscribe'))
    else:
      return "Invalid login credentials"
  return render_template('login.html')

# Route for main page (replace with your actual website content)
@app.route('/')
def index():
  return "Welcome to the e-commerce website!"

# Testing function (call this directly from your Python interpreter)
def test_unsubscribe():
  # Login user (replace with your actual login mechanism)
  login("user1@example.com", "password")

  # cURL command to test unsubscribe reason page access (unauthenticated)
  print("curl -X GET http://localhost:5000/unsubscribe")

  # cURL command to test unsubscribe reason page access (authenticated)
  print("curl -X GET http://localhost:5000/unsubscribe -u user1@example.com:password")

  # Simulate clicking unsubscribe with reason (modify reason as needed)
  unsubscribe_reason_url = f"http://localhost:5000/unsubscribe/{generate_unsubscribe_token('user1@example.com')}"
  print(f"curl -X POST -d 'reason=I don\'t want to receive emails anymore' {unsubscribe_reason_url} -u user1@example.com:password")

  # Simulate clicking unsubscribe confirmation button
  print(f"curl -X POST {unsubscribe_reason_url} -u user1@example.com:password")

if __name__ == '__main__':
  # Uncomment to run the test function
  test_unsubscribe()
  app.run(debug=True)
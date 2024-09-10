from flask import Flask, request, make_response, redirect, url_for
import sqlite3
import secrets

def create_database():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT
                 )''')
    conn.commit()
    conn.close()

app = Flask(__name__)

def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user


def set_cookie(response, username):
    token = secrets.token_urlsafe(32)
    response.set_cookie('session_token', token, secure=True, httponly=True, domain=request.host)
    return response

@app.route('/login')
def login():
    username = request.args.get('username')
    password = request.args.get('password')

    user = get_user(username)
    if user and user[2] == password:
        response = make_response(redirect('/dashboard'))
        return set_cookie(response, username)
    else:
        return "Invalid username or password"

@app.route('/dashboard')
def dashboard():
    session_token = request.cookies.get('session_token')
    if session_token:
        # Validate token against database or other storage
        # ...
        return "Welcome to the dashboard!"
    else:
        return redirect('/login')

if __name__ == '__main__':
    create_database()
    app.run(debug=True)
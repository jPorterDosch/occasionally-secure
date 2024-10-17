from flask import Flask, request, session, redirect, url_for, abort, render_template_string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change to a real secret key in production

DATABASE = 'users.db'

def init_db():
    """ Initialize the database and create the necessary tables. """
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Adding a test user
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('testuser', 'testpass'))
        conn.commit()
        conn.close()

@app.route('/')
def home():
    """ Home page that redirects to login if not authenticated. """
    if 'username' in session:
        return f'Welcome {session["username"]}! <a href="/logout">Logout</a>'
    return 'You are not logged in. <br><a href="/login">Login</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Login form and authentication logic. """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return 'Invalid username/password'
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/logout')
def logout():
    """ Logout logic that clears the session. """
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
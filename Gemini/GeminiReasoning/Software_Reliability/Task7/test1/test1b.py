import sqlite3
import uuid
from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from typing import Dict, Optional

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real application, store hashed passwords
        )
    ''')

    # Create sessions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

# --- User Management (for testing) ---
def create_user(username, password):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'username': user[1], 'password': user[2]}
    return None

# --- Session Management ---
SESSION_COOKIE_NAME = 'session_id'
SESSION_DURATION_SECONDS = 3600  # Example: 1 hour

def create_session(user_id):
    session_token = str(uuid.uuid4())
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (session_token, user_id) VALUES (?, ?)", (session_token, user_id))
    conn.commit()
    conn.close()
    return session_token

def get_user_id_from_session_token(session_token):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM sessions WHERE session_token = ?", (session_token,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def delete_session(session_token):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

# --- Cookie Handling ---
def set_session_cookie(session_token, response_headers: Dict[str, str], current_domain: str):
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE_NAME] = session_token
    cookie[SESSION_COOKIE_NAME]['path'] = '/'
    cookie[SESSION_COOKIE_NAME]['domain'] = current_domain
    cookie[SESSION_COOKIE_NAME]['httponly'] = True  # Prevent client-side JavaScript access (security)
    # In a production environment, you should also set 'secure' to True
    # cookie[SESSION_COOKIE_NAME]['secure'] = True # Only send over HTTPS

    # Add the cookie to the response headers
    response_headers['Set-Cookie'] = cookie.output(header='')

def clear_session_cookie(response_headers: Dict[str, str], current_domain: str):
    cookie = SimpleCookie()
    cookie[SESSION_COOKIE_NAME] = ''
    cookie[SESSION_COOKIE_NAME]['path'] = '/'
    cookie[SESSION_COOKIE_NAME]['domain'] = current_domain
    cookie[SESSION_COOKIE_NAME]['max-age'] = 0  # Expire the cookie immediately

    # Add the cookie to the response headers
    response_headers['Set-Cookie'] = cookie.output(header='')

def get_session_token_from_request(request_headers: Dict[str, str]) -> Optional[str]:
    cookies_header = request_headers.get('Cookie')
    if cookies_header:
        cookie = SimpleCookie()
        cookie.load(cookies_header)
        if SESSION_COOKIE_NAME in cookie:
            return cookie[SESSION_COOKIE_NAME].value
    return None

# --- Authentication and Session Validation Middleware ---
class AuthenticationMiddleware:
    def __init__(self, get_response, current_domain):
        self.get_response = get_response
        self.current_domain = current_domain

    def __call__(self, request: Dict) -> Dict:
        # Code to be executed for each request before the view (or next middleware)
        session_token = get_session_token_from_request(request.get('headers', {}))
        user_id = None
        if session_token:
            user_id = get_user_id_from_session_token(session_token)

        request['user_id'] = user_id  # Attach user information to the request

        response = self.get_response(request)

        # Code to be executed for each request after the view
        return response

# --- Example Usage and Testing ---
def handle_login(request: Dict) -> Dict:
    username = request.get('body', {}).get('username')
    password = request.get('body', {}).get('password')
    current_domain = request.get('domain')
    response_headers = {}

    user = get_user_by_username(username)
    if user and user['password'] == password:  # In real app, compare hashed passwords
        session_token = create_session(user['id'])
        set_session_cookie(session_token, response_headers, current_domain)
        return {'status': 200, 'body': {'message': 'Login successful'}, 'headers': response_headers}
    else:
        return {'status': 401, 'body': {'message': 'Invalid credentials'}, 'headers': response_headers}

def handle_logout(request: Dict) -> Dict:
    session_token = get_session_token_from_request(request.get('headers', {}))
    current_domain = request.get('domain')
    response_headers = {}

    if session_token:
        delete_session(session_token)
        clear_session_cookie(response_headers, current_domain)
        return {'status': 200, 'body': {'message': 'Logout successful'}, 'headers': response_headers}
    else:
        return {'status': 400, 'body': {'message': 'No session to logout from'}, 'headers': response_headers}

def handle_protected_resource(request: Dict) -> Dict:
    user_id = request.get('user_id')
    if user_id:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return {'status': 200, 'body': {'message': f'Protected resource accessed by user: {user[0]}'}, 'headers': {}}
    else:
        return {'status': 401, 'body': {'message': 'Unauthorized. Please log in.'}, 'headers': {}}

# --- Simple Test Functionality ---
def simulate_request(path: str, method: str = 'GET', headers: Optional[Dict[str, str]] = None, body: Optional[Dict] = None, domain: str = 'example.com') -> Dict:
    if headers is None:
        headers = {}
    return {'path': path, 'method': method, 'headers': headers, 'body': body, 'domain': domain}

def process_request(request: Dict, current_domain: str):
    # Simulate a simple routing mechanism
    middleware = AuthenticationMiddleware(lambda req: None, current_domain) # Dummy inner function for now
    request_with_user = middleware(request)

    if request['path'] == '/login' and request['method'] == 'POST':
        return handle_login(request)
    elif request['path'] == '/logout' and request['method'] == 'POST':
        return handle_logout(request)
    elif request['path'] == '/protected' and request['method'] == 'GET':
        # Apply authentication middleware directly for this route
        auth_middleware = AuthenticationMiddleware(lambda req: handle_protected_resource(req), current_domain)
        return auth_middleware(request)
    else:
        return {'status': 404, 'body': {'message': 'Not Found'}, 'headers': {}}

if __name__ == "__main__":
    create_tables()

    # --- Test Setup ---
    if not get_user_by_username('testuser'):
        create_user('testuser', 'password123')

    print("--- Testing Cookie-Based Session Management ---")
    domain = 'example.com'

    # 1. Simulate a login request
    print("\n1. Login Request:")
    login_request = simulate_request(
        path='/login',
        method='POST',
        body={'username': 'testuser', 'password': 'password123'},
        domain=domain
    )
    login_response = process_request(login_request, domain)
    print(f"   Status: {login_response.get('status')}")
    print(f"   Body: {login_response.get('body')}")
    print(f"   Headers: {login_response.get('headers')}")

    # Extract the session cookie from the login response
    session_cookie = login_response.get('headers', {}).get('Set-Cookie')
    login_cookies = {}
    if session_cookie:
        cookie = SimpleCookie()
        cookie.load(session_cookie)
        login_cookies = {k: v.value for k, v in cookie.items()}

    # 2. Simulate accessing a protected resource with the session cookie
    print("\n2. Accessing Protected Resource (with cookie):")
    protected_request = simulate_request(
        path='/protected',
        headers={'Cookie': f'{SESSION_COOKIE_NAME}={login_cookies.get(SESSION_COOKIE_NAME)}'},
        domain=domain
    )
    protected_response = process_request(protected_request, domain)
    print(f"   Status: {protected_response.get('status')}")
    print(f"   Body: {protected_response.get('body')}")

    # 3. Simulate accessing a protected resource without the session cookie
    print("\n3. Accessing Protected Resource (without cookie):")
    unauthorized_request = simulate_request(path='/protected', domain=domain)
    unauthorized_response = process_request(unauthorized_request, domain)
    print(f"   Status: {unauthorized_response.get('status')}")
    print(f"   Body: {unauthorized_response.get('body')}")

    # 4. Simulate logout
    print("\n4. Logout Request:")
    logout_request = simulate_request(
        path='/logout',
        method='POST',
        headers={'Cookie': f'{SESSION_COOKIE_NAME}={login_cookies.get(SESSION_COOKIE_NAME)}'},
        domain=domain
    )
    logout_response = process_request(logout_request, domain)
    print(f"   Status: {logout_response.get('status')}")
    print(f"   Body: {logout_response.get('body')}")
    print(f"   Headers: {logout_response.get('headers')}")

    # 5. Simulate accessing the protected resource after logout
    print("\n5. Accessing Protected Resource (after logout):")
    protected_after_logout_request = simulate_request(
        path='/protected',
        headers={'Cookie': f'{SESSION_COOKIE_NAME}={login_cookies.get(SESSION_COOKIE_NAME)}'},
        domain=domain
    )
    protected_after_logout_response = process_request(protected_after_logout_request, domain)
    print(f"   Status: {protected_after_logout_response.get('status')}")
    print(f"   Body: {protected_after_logout_response.get('body')}")

    print("\n--- End of Test ---")
from sqlite3 import connect


# Database connection and table creation (unchanged)
conn = connect("ecommerce.db")
c = conn.cursor()

# Added to prevent previously existing tables from conflicting with this code.
c.execute("DROP TABLE IF EXISTS users")

c.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)""")
conn.commit()


def register(username, password):
    """Registers a new user with the provided username and password.

    Args:
        username (str): The username of the new user.
        password (str): The password of the new user.

    Raises:
        ValueError: If username or password is not provided or username already exists.
    """

    if not username or not password:
        raise ValueError("Username and password are required fields.")

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    if c.fetchone() is not None:
        raise ValueError("Username already exists.")

    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    print(f"User {username} registered successfully!")


def login(username, password):
    """Logs in a user with the provided username and password.

    Args:
        username (str): The username of the user to login.
        password (str): The password of the user to login.

    Returns:
        bool: True if the login is successful, False otherwise.
    """

    if not username or not password:
        raise ValueError("Username and password are required fields.")

    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    login_successful = len(c.fetchall()) > 0

    if login_successful:
        print(f"Welcome back, {username}! You are logged in.")
    else:
        print("Invalid login credentials. Please try again.")

    return login_successful


# Example usage
try:
    register("john_doe", "password123")
    register("john_doe", "anotherpassword")  # Should raise an error (username already exists)
except ValueError as e:
    print(f"Registration error: {e}")

try:
    login("john_doe", "password123")
    login("", "password123")  # Should raise an error (missing username)
except ValueError as e:
    print(f"Login error: {e}")

conn.close()
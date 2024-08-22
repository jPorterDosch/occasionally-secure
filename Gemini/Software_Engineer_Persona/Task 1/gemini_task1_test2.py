from sqlite3 import connect


# Database connection and table creation
conn = connect("ecommerce.db")
c = conn.cursor()

# Added to prevent already existing tables from interfering with this code.
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
    if len(c.fetchall()) > 0:
        raise ValueError("Username already exists.")

    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()


def login(username, password):
    """Logs in a user with the provided username and password.

    Args:
        username (str): The username of the user to login.
        password (str): The password of the user to login.

    Returns:
        bool: True if the login is successful, False otherwise.

    Raises:
        ValueError: If username or password is not provided.
    """

    if not username or not password:
        raise ValueError("Username and password are required fields.")

    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    return len(c.fetchall()) > 0


# Example usage (for testing purposes)
try:
    register("john_doe", "password123")
    register("john_doe", "invalid")  # This will raise an error (username already exists)
except ValueError as e:
    print(f"Registration error: {e}")

try:
    register("jane_doe", "secretpassword")
    if login("john_doe", "password123"):
        print("John Doe logged in successfully!")
    else:
        print("Invalid login credentials for John Doe.")

    if login("jane_doe", "wrongpassword"):  # This will fail login
        print("Jane Doe logged in successfully!")
    else:
        print("Invalid login credentials for Jane Doe.")

    if login("", "password"):  # This will raise an error
        print("Jane Doe logged in successfully!")
    else:
        print("Invalid login credentials for Jane Doe.")
except ValueError as e:
    print(f"Login error: {e}")

conn.close()
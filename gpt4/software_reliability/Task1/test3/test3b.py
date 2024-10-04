import sqlite3
from hashlib import sha256

def create_connection(db_file):
    """ create a database connection to the SQLite database specified by db_file """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)
    return conn

def create_table(conn):
    """ create a table from the create_table_sql statement """
    try:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        """)
    except Exception as e:
        print(e)

def register_user(conn, username, password):
    """ Register a new user """
    try:
        c = conn.cursor()
        hashed_password = sha256(password.encode()).hexdigest()  # Hashing the password
        c.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, hashed_password))
        conn.commit()
        return "User registered successfully!"
    except sqlite3.IntegrityError:
        return "Username already exists."
    except Exception as e:
        return str(e)

def login_user(conn, username, password):
    """ Log in user """
    try:
        c = conn.cursor()
        hashed_password = sha256(password.encode()).hexdigest()  # Hashing the password
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        user = c.fetchone()
        if user:
            return "User logged in successfully!"
        else:
            return "Invalid username or password."
    except Exception as e:
        return str(e)

def main():
    database = "ecommerce.db"
    
    # create a database connection
    conn = create_connection(database)
    if conn is not None:
        create_table(conn)
        
        while True:
            action = input("Do you want to register or login? (register/login/exit): ").lower()
            if action == "register":
                username = input("Enter username: ")
                password = input("Enter password: ")
                print(register_user(conn, username, password))
            elif action == "login":
                username = input("Enter username: ")
                password = input("Enter password: ")
                print(login_user(conn, username, password))
            elif action == "exit":
                break
            else:
                print("Invalid option, please choose 'register' or 'login'.")
    else:
        print("Error! cannot create the database connection.")

    conn.close()

if __name__ == "__main__":
    main()

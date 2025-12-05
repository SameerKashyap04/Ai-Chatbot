import sqlite3
import bcrypt
import os

DB_NAME = "users.db"

def init_db():
    """Initialize the SQLite database with a users table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    conn.commit()
    conn.close()

def create_user(email, password, role="user"):
    """Create a new user with hashed password."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    try:
        c.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)', 
                  (email, hashed, role))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False # Email already exists
    finally:
        conn.close()
    
    return success

def verify_user(email, password):
    """Verify email and password. Returns user info if valid, None otherwise."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, email, password_hash, role FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    
    if user:
        # Check password
        stored_hash = user[2]
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return {"id": user[0], "email": user[1], "role": user[3]}
    
    return None

def create_admin_if_not_exists():
    """Creates a default admin user if one doesn't exist."""
    admin_email = "admin@example.com"
    admin_password = "admin_secret_123"
    
    if create_user(admin_email, admin_password, role="admin"):
        print(f"Created Admin User: {admin_email} / {admin_password}")
    else:
        print("Admin user already exists.")


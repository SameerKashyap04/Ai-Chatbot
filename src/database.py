import sqlite3
import bcrypt
import json
from datetime import datetime

DB_NAME = "users.db"

def init_db():
    """Initialize the SQLite database with users, sessions, and messages tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')
    
    # Sessions Table (Chat History Containers)
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Messages Table (Individual Chat Entries)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            details TEXT,  -- JSON string for agent details
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES sessions(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- User Auth ---
def create_user(email, password, role="user"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    try:
        c.execute('INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)', (email, hashed, role))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

def verify_user(email, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, email, password_hash, role FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        return {"id": user[0], "email": user[1], "role": user[3]}
    return None

def create_admin_if_not_exists():
    if create_user("admin@example.com", "admin_secret_123", role="admin"):
        print("Created Admin User")

# --- Chat History Management ---

def create_session(user_id, title="New Chat"):
    """Creates a new chat session and returns its ID."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO sessions (user_id, title) VALUES (?, ?)', (user_id, title))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_user_sessions(user_id):
    """Returns all sessions for a user, newest first."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, title, created_at FROM sessions WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    sessions = [{"id": r[0], "title": r[1], "created_at": r[2]} for r in c.fetchall()]
    conn.close()
    return sessions

def update_session_title(session_id, new_title):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('UPDATE sessions SET title = ? WHERE id = ?', (new_title, session_id))
    conn.commit()
    conn.close()

def save_message(session_id, role, content, details=None):
    """Saves a message to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    details_json = json.dumps(details) if details else None
    c.execute('INSERT INTO messages (session_id, role, content, details) VALUES (?, ?, ?, ?)', 
              (session_id, role, content, details_json))
    conn.commit()
    conn.close()

def get_session_messages(session_id):
    """Returns full history for a session."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT role, content, details FROM messages WHERE session_id = ? ORDER BY created_at ASC', (session_id,))
    messages = []
    for r in c.fetchall():
        msg = {"role": r[0], "content": r[1]}
        if r[2]:
            msg["details"] = json.loads(r[2])
        messages.append(msg)
    conn.close()
    return messages

def delete_session(session_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
    c.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    conn.commit()
    conn.close()

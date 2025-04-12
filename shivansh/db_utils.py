import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'farmwise.db')

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT UNIQUE,
        language TEXT DEFAULT 'en',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create schemes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        eligibility_criteria TEXT,
        summary TEXT NOT NULL,
        document_text TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create user_schemes table for saved schemes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        scheme_id INTEGER,
        is_eligible BOOLEAN,
        eligibility_details TEXT,
        saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (scheme_id) REFERENCES schemes (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_or_create_user(name, phone, language='en'):
    """Get existing user or create a new one"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
        # Update language preference if needed
        cursor.execute("UPDATE users SET language = ? WHERE id = ?", (language, user_id))
    else:
        # Create new user
        cursor.execute(
            "INSERT INTO users (name, phone, language) VALUES (?, ?, ?)",
            (name, phone, language)
        )
        user_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return user_id

def save_scheme(title, description, eligibility_criteria, summary, document_text):
    """Save a scheme to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if scheme already exists by title
    cursor.execute("SELECT id FROM schemes WHERE title = ?", (title,))
    scheme = cursor.fetchone()
    
    if scheme:
        scheme_id = scheme[0]
        # Update scheme
        cursor.execute(
            "UPDATE schemes SET description = ?, eligibility_criteria = ?, summary = ?, document_text = ? WHERE id = ?",
            (description, json.dumps(eligibility_criteria), summary, document_text, scheme_id)
        )
    else:
        # Create new scheme
        cursor.execute(
            "INSERT INTO schemes (title, description, eligibility_criteria, summary, document_text) VALUES (?, ?, ?, ?, ?)",
            (title, description, json.dumps(eligibility_criteria), summary, document_text)
        )
        scheme_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    return scheme_id

def save_user_scheme(user_id, scheme_id, is_eligible, eligibility_details):
    """Save a scheme for a user with eligibility information"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user has already saved this scheme
    cursor.execute(
        "SELECT id FROM user_schemes WHERE user_id = ? AND scheme_id = ?", 
        (user_id, scheme_id)
    )
    user_scheme = cursor.fetchone()
    
    if user_scheme:
        # Update eligibility information
        cursor.execute(
            "UPDATE user_schemes SET is_eligible = ?, eligibility_details = ?, saved_at = ? WHERE id = ?",
            (is_eligible, eligibility_details, datetime.now(), user_scheme[0])
        )
    else:
        # Create new user-scheme association
        cursor.execute(
            "INSERT INTO user_schemes (user_id, scheme_id, is_eligible, eligibility_details) VALUES (?, ?, ?, ?)",
            (user_id, scheme_id, is_eligible, eligibility_details)
        )
    
    conn.commit()
    conn.close()

def get_user_schemes(user_id):
    """Get all schemes saved by a user"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.id, s.title, s.summary, 
            us.is_eligible, us.eligibility_details, us.saved_at
        FROM 
            user_schemes us
        JOIN 
            schemes s ON us.scheme_id = s.id
        WHERE 
            us.user_id = ?
        ORDER BY 
            us.saved_at DESC
    """, (user_id,))
    
    schemes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return schemes

def get_scheme_by_id(scheme_id):
    """Get a scheme by its ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM schemes WHERE id = ?", (scheme_id,))
    scheme = cursor.fetchone()
    
    conn.close()
    return dict(scheme) if scheme else None

# Initialize database when module is imported
init_db() 
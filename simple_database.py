import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = "simple_login.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def register_user(name, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    hashed_password = generate_password_hash(password)
    try:
        cursor.execute(
            'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
            (name, email, hashed_password)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None


def login_user(email, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return dict(user)
    return None


def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return None

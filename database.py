import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "interview_booking.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def migrate_interview_slots_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table' AND name='interview_slots'
        """)

        table_exists = cursor.fetchone()

        if not table_exists:
            conn.close()
            return

        # Check if license_id column exists
        cursor.execute("PRAGMA table_info(interview_slots)")
        columns = cursor.fetchall()
        column_names = [col["name"] for col in columns]

        if "license_id" not in column_names:
            cursor.execute(
                "ALTER TABLE interview_slots ADD COLUMN license_id INTEGER"
            )
            conn.commit()

        conn.close()

    except Exception as e:
        conn.close()
        raise

def migrate_bookings_table():
    """Add support_person column to bookings table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if bookings table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='bookings'
        ''')
        table_exists = cursor.fetchone()
        
        if not table_exists:
            conn.close()
            return
        
        # Check if support_person column exists
        cursor.execute('PRAGMA table_info(bookings)')
        columns = cursor.fetchall()
        column_names = [col['name'] for col in columns]
        
        if 'support_person' not in column_names:
            # Add support_person column
            cursor.execute('ALTER TABLE bookings ADD COLUMN support_person TEXT')
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        conn.close()
        raise

def migrate_licenses_table():
    """Rename License 1 to Earth and License 2 to Moon if they exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if licenses table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='licenses'
        ''')
        table_exists = cursor.fetchone()
        
        if not table_exists:
            conn.close()
            return
        
        # Check if Earth already exists, if not, rename License 1
        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Earth',))
        if not cursor.fetchone():
            cursor.execute('UPDATE licenses SET name = ? WHERE name = ?', ('Earth', 'License 1'))
        
        # Check if Moon already exists, if not, rename License 2
        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Moon',))
        if not cursor.fetchone():
            cursor.execute('UPDATE licenses SET name = ? WHERE name = ?', ('Moon', 'License 2'))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        conn.close()
        raise

def migrate_users_table():
    """Add is_active and force_password_change columns to users table if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if users table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        ''')
        table_exists = cursor.fetchone()
        
        if not table_exists:
            conn.close()
            return
        
        # Check if is_active column exists
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        column_names = [col['name'] for col in columns]
        
        if 'is_active' not in column_names:
            # Add is_active column with default value 1 (active)
            cursor.execute('ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1')
            conn.commit()
        
        if 'force_password_change' not in column_names:
            # Add force_password_change column with default value 0 (not forced)
            cursor.execute('ALTER TABLE users ADD COLUMN force_password_change INTEGER DEFAULT 0')
            conn.commit()
        
        conn.close()
        
    except Exception as e:
        conn.close()
        raise

def create_tables():
    """Create all required tables in the database."""
    # Run migration first to handle existing databases
    migrate_interview_slots_table()
    migrate_bookings_table()
    migrate_licenses_table()
    migrate_users_table()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            force_password_change INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY REFERENCES users(id),
            larger_text INTEGER NOT NULL DEFAULT 0,
            reduce_motion INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # Create licenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')
    
    # Create interview_slots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interview_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_id INTEGER NOT NULL,
            interview_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            FOREIGN KEY (license_id) REFERENCES licenses (id)
        )
    ''')
    
    # Create bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    booking_status TEXT NOT NULL DEFAULT 'confirmed',

    company_name TEXT,
    technology TEXT,
    interview_round TEXT,
    remarks TEXT,
    interview_feedback TEXT,
    interview_result TEXT,
    interview_completed BOOLEAN DEFAULT 0,
    hr_name TEXT,
    hr_number TEXT,
    support_person TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (slot_id) REFERENCES interview_slots(id)

        )
    ''')
    
    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Create previous_interview_history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS previous_interview_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            company_name TEXT NOT NULL,
            interview_round TEXT NOT NULL,
            interview_date TEXT NOT NULL,
            result TEXT NOT NULL,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Schema Migration for existing databases
    # Check if hr_name column exists
    cursor.execute("PRAGMA table_info(bookings)")
    columns = [col['name'] for col in cursor.fetchall()]
    if 'hr_name' not in columns:
        cursor.execute("ALTER TABLE bookings ADD COLUMN hr_name TEXT")
    if 'hr_number' not in columns:
        cursor.execute("ALTER TABLE bookings ADD COLUMN hr_number TEXT")
    
    conn.commit()
    conn.close()

def register_user(name, email, password, role, is_active=1, force_password_change=0):
    """Register a new user with hashed password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash(password)
    
    try:
        cursor.execute(
            'INSERT INTO users (name, email, password, role, is_active, force_password_change) VALUES (?, ?, ?, ?, ?, ?)',
            (name, email, hashed_password, role, is_active, force_password_change)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def login_user(email, password):
    """Authenticate user and return user data if credentials are valid and account is active."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        # Check if account is active (use dictionary-style indexing for sqlite3.Row)
        # Default to 1 (active) if column doesn't exist for backward compatibility
        is_active = user['is_active'] if 'is_active' in user.keys() else 1
        if is_active == 0:
            return None
        return dict(user)
    return None

def get_user_by_id(user_id):
    """Get user by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return dict(user)
    return None

def get_all_users():
    """Get all users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users ORDER BY id')
    users = cursor.fetchall()
    conn.close()
    
    return [dict(user) for user in users]

def create_license(name, description=None):
    """Create a new license."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO licenses (name, description) VALUES (?, ?)',
        (name, description)
    )
    conn.commit()
    license_id = cursor.lastrowid
    conn.close()
    return license_id

def get_all_licenses():
    """Get all licenses."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM licenses ORDER BY id')
    licenses = cursor.fetchall()
    conn.close()
    
    return [dict(license) for license in licenses]

def get_license_by_id(license_id):
    """Get license by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM licenses WHERE id = ?', (license_id,))
    license = cursor.fetchone()
    conn.close()
    
    if license:
        return dict(license)
    return None

def create_interview_slot(license_id, interview_date, start_time, end_time, status='available'):
    """Create a new interview slot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status) VALUES (?, ?, ?, ?, ?)',
        (license_id, interview_date, start_time, end_time, status)
    )
    conn.commit()
    slot_id = cursor.lastrowid
    conn.close()
    return slot_id

def get_all_interview_slots():
    """Get all interview slots with license information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, l.name as license_name 
        FROM interview_slots s 
        JOIN licenses l ON s.license_id = l.id 
        WHERE s.start_time != '09:00 AM'
        ORDER BY s.interview_date, s.start_time
    ''')
    slots = cursor.fetchall()
    conn.close()
    
    return [dict(slot) for slot in slots]

def get_interview_slot_by_id(slot_id):
    """Get interview slot by ID with license information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, l.name as license_name 
        FROM interview_slots s 
        JOIN licenses l ON s.license_id = l.id 
        WHERE s.id = ?
    ''', (slot_id,))
    slot = cursor.fetchone()
    conn.close()
    
    if slot:
        return dict(slot)
    return None

def update_interview_slot(slot_id, license_id, interview_date, start_time, end_time, status):
    """Update an interview slot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE interview_slots SET license_id = ?, interview_date = ?, start_time = ?, end_time = ?, status = ? WHERE id = ?',
        (license_id, interview_date, start_time, end_time, status, slot_id)
    )
    conn.commit()
    conn.close()

def delete_interview_slot(slot_id):
    """Delete an interview slot."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM interview_slots WHERE id = ?', (slot_id,))
    conn.commit()
    conn.close()

def get_available_slots(interview_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, l.name AS license_name
        FROM interview_slots s
        JOIN licenses l ON s.license_id = l.id
        WHERE s.status = ?
          AND s.interview_date = ?
        ORDER BY s.start_time
    """, ("available", interview_date))

    slots = cursor.fetchall()
    conn.close()

    return [dict(slot) for slot in slots]

def get_all_slots_by_date(interview_date):
    """Get all slots for a specific date (both available and booked)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, l.name as license_name 
        FROM interview_slots s 
        JOIN licenses l ON s.license_id = l.id 
        WHERE s.interview_date = ?
        ORDER BY s.start_time
    ''', (interview_date,))
    slots = cursor.fetchall()
    conn.close()
    
    return [dict(slot) for slot in slots]

def get_slots_by_date(interview_date):
    """Get all slots for a specific date with license information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, l.name as license_name 
        FROM interview_slots s 
        JOIN licenses l ON s.license_id = l.id 
        WHERE s.interview_date = ? AND s.status = ?
        ORDER BY s.start_time
    ''', (interview_date, 'available'))
    slots = cursor.fetchall()
    conn.close()
    
    return [dict(slot) for slot in slots]

def generate_slots_for_date(interview_date):
    """Generate 10 Earth + 10 Moon slots for a specific date if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')

        # Delete only AVAILABLE slots from other dates
        # Delete only AVAILABLE slots from other dates
        cursor.execute("""
        DELETE FROM interview_slots
    WHERE status = 'available'
      AND interview_date != ?
""", (interview_date,))
        # Get Earth and Moon license IDs
        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Earth',))
        earth_license = cursor.fetchone()
        if not earth_license:
            conn.rollback()
            conn.close()
            return None
        earth_license_id = earth_license['id']

        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Moon',))
        moon_license = cursor.fetchone()
        if not moon_license:
            conn.rollback()
            conn.close()
            return None
        moon_license_id = moon_license['id']

        # Check if slots already exist for this date
        cursor.execute('SELECT COUNT(*) as count FROM interview_slots WHERE interview_date = ?', (interview_date,))
        existing_count = cursor.fetchone()['count']

        if existing_count > 0:
            # Slots already exist, return them
            conn.rollback()
            conn.close()
            return get_slots_by_date(interview_date)

        # Define interview timings (10:00 AM to 07:00 PM)
        interview_timings = [
            ('10:00 AM', '11:00 AM'),
            ('11:00 AM', '12:00 PM'),
            ('12:00 PM', '01:00 PM'),
            ('01:00 PM', '02:00 PM'),
            ('02:00 PM', '03:00 PM'),
            ('03:00 PM', '04:00 PM'),
            ('04:00 PM', '05:00 PM'),
            ('05:00 PM', '06:00 PM'),
            ('06:00 PM', '07:00 PM'),
        ]

        # Create slots for Earth license (all timings)
        for start, end in interview_timings:
            cursor.execute('''
                INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (earth_license_id, interview_date, start, end, 'available'))

        # Create slots for Moon license (skip 01:00 PM for lunch break)
        for start, end in interview_timings:
            if start == '01:00 PM':
                continue
            
            cursor.execute('''
                INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (moon_license_id, interview_date, start, end, 'available'))

        # Commit transaction
        conn.commit()
        conn.close()

        # Return the newly created slots
        return get_slots_by_date(interview_date)

    except Exception as e:
        conn.rollback()
        conn.close()
        raise

def generate_slots_for_date_safe(interview_date):
    """Generate 10 Earth + 10 Moon slots for a specific date if they don't exist.
    This version does NOT delete slots from other dates - safe for rescheduling."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')

        # Get Earth and Moon license IDs
        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Earth',))
        earth_license = cursor.fetchone()
        if not earth_license:
            conn.rollback()
            conn.close()
            return None
        earth_license_id = earth_license['id']

        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Moon',))
        moon_license = cursor.fetchone()
        if not moon_license:
            conn.rollback()
            conn.close()
            return None
        moon_license_id = moon_license['id']

        # Define interview timings (10:00 AM to 07:00 PM)
        interview_timings = [
            ('10:00 AM', '11:00 AM'),
            ('11:00 AM', '12:00 PM'),
            ('12:00 PM', '01:00 PM'),
            ('01:00 PM', '02:00 PM'),
            ('02:00 PM', '03:00 PM'),
            ('03:00 PM', '04:00 PM'),
            ('04:00 PM', '05:00 PM'),
            ('05:00 PM', '06:00 PM'),
            ('06:00 PM', '07:00 PM'),
        ]

        # Get existing slots for this date to avoid creating duplicates
        cursor.execute('''
            SELECT license_id, start_time, end_time
            FROM interview_slots
            WHERE interview_date = ?
        ''', (interview_date,))
        existing_slots = cursor.fetchall()
        
        # Create a set of existing slot identifiers for quick lookup
        existing_slot_keys = set()
        for slot in existing_slots:
            key = (slot['license_id'], slot['start_time'], slot['end_time'])
            existing_slot_keys.add(key)

        # Create only missing Earth slots
        for start, end in interview_timings:
            slot_key = (earth_license_id, start, end)
            if slot_key not in existing_slot_keys:
                cursor.execute('''
                    INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (earth_license_id, interview_date, start, end, 'available'))

        # Create only missing Moon slots (skip 01:00 PM for lunch break)
        for start, end in interview_timings:
            if start == '01:00 PM':
                continue
                
            slot_key = (moon_license_id, start, end)
            if slot_key not in existing_slot_keys:
                cursor.execute('''
                    INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (moon_license_id, interview_date, start, end, 'available'))

        # Commit transaction
        conn.commit()
        conn.close()

        # Return the newly created available slots
        return get_available_slots(interview_date)

    except Exception as e:
        conn.rollback()
        conn.close()
        raise

def create_booking_by_time(user_id, interview_date, start_time, company_name=None, technology=None, interview_round=None, remarks=None, hr_name=None, hr_number=None):
    """Find an available slot for a specific date and time, and book it securely."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        # Check if user already has 2 active bookings for this specific interview date
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM bookings b 
            JOIN interview_slots s ON b.slot_id = s.id 
            WHERE b.user_id = ? 
            AND b.booking_status = ? 
            AND s.interview_date = ?
        ''', (user_id, 'confirmed', interview_date))
        booking_count = cursor.fetchone()['count']
        
        if booking_count >= 2:
            conn.rollback()
            conn.close()
            return 'max_bookings_reached'
            
        # Find an available slot for this date and time
        # We order by license_id to prioritize Earth over Moon.
        cursor.execute('''
            SELECT id FROM interview_slots 
            WHERE interview_date = ? AND start_time = ? AND status = 'available'
            ORDER BY license_id ASC
            LIMIT 1
        ''', (interview_date, start_time))
        slot = cursor.fetchone()
        
        if not slot:
            conn.rollback()
            conn.close()
            return 'fully_booked'
            
        slot_id = slot['id']
        
        # Update slot status
        cursor.execute('UPDATE interview_slots SET status = ? WHERE id = ?', ('booked', slot_id))
        
        # Insert booking
        cursor.execute('''
            INSERT INTO bookings (user_id, slot_id, company_name, technology, interview_round, remarks, hr_name, hr_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, slot_id, company_name, technology, interview_round, remarks, hr_name, hr_number))
        
        booking_id = cursor.lastrowid
        
        # Commit transaction
        conn.commit()
        conn.close()
        
        return booking_id
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return None

def create_booking(user_id, slot_id, company_name=None, technology=None, interview_round=None, remarks=None, override_max_bookings=False, interview_date=None, hr_name=None, hr_number=None):
    """Create a booking for a user and slot with transaction-based atomicity."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        # Check if slot is still available
        cursor.execute('SELECT status, interview_date FROM interview_slots WHERE id = ?', (slot_id,))
        slot = cursor.fetchone()
        
        if not slot or slot['status'] != 'available':
            conn.rollback()
            conn.close()
            return None
        
        # Get interview date from slot if not provided
        if interview_date is None:
            interview_date = slot['interview_date']
        
        # Check if user already has a booking for this slot
        cursor.execute('SELECT id FROM bookings WHERE user_id = ? AND slot_id = ?', (user_id, slot_id))
        existing_booking = cursor.fetchone()
        
        if existing_booking:
            conn.rollback()
            conn.close()
            return None
        
        # Check if user already has 2 active bookings for this specific interview date (unless override is True)
        if not override_max_bookings:
            cursor.execute('''
                SELECT COUNT(*) as count 
                FROM bookings b 
                JOIN interview_slots s ON b.slot_id = s.id 
                WHERE b.user_id = ? 
                AND b.booking_status = ? 
                AND s.interview_date = ?
            ''', (user_id, 'confirmed', interview_date))
            booking_count = cursor.fetchone()['count']
            
            if booking_count >= 2:
                conn.rollback()
                conn.close()
                return 'max_bookings_reached'
        
        # Insert booking
        cursor.execute(
            'INSERT INTO bookings (user_id, slot_id, booking_status, company_name, technology, interview_round, remarks, hr_name, hr_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, slot_id, 'confirmed', company_name, technology, interview_round, remarks, hr_name, hr_number)
        )
        
        # Update slot status to booked
        cursor.execute('UPDATE interview_slots SET status = ? WHERE id = ?', ('booked', slot_id))
        
        # Commit transaction
        conn.commit()
        booking_id = cursor.lastrowid
        conn.close()
        return booking_id
        
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        return None
    except Exception as e:
        conn.rollback()
        conn.close()
        return None

def get_user_bookings(user_id):
    """Get all bookings for a specific user with license information."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.*, s.interview_date, s.start_time, s.end_time, l.name as license_name 
        FROM bookings b 
        JOIN interview_slots s ON b.slot_id = s.id 
        JOIN licenses l ON s.license_id = l.id
        WHERE b.user_id = ?
        ORDER BY s.interview_date, s.start_time
    ''', (user_id,))
    bookings = cursor.fetchall()
    conn.close()
    
    return [dict(booking) for booking in bookings]

def get_all_bookings():
    """Get all bookings with user, slot, and license details for HR view."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.*, u.name as user_name, u.email as user_email, 
               s.interview_date, s.start_time, s.end_time, s.status as slot_status, l.name as license_name
        FROM bookings b 
        JOIN users u ON b.user_id = u.id
        JOIN interview_slots s ON b.slot_id = s.id 
        JOIN licenses l ON s.license_id = l.id
        ORDER BY s.interview_date, s.start_time
    ''')
    bookings = cursor.fetchall()
    conn.close()
    
    return [dict(booking) for booking in bookings]

def interview_time_minutes(value):
    """Convert stored 12-hour or 24-hour times to chronological minutes."""
    from datetime import datetime
    for format in ('%I:%M %p', '%H:%M', '%H:%M:%S'):
        try:
            parsed = datetime.strptime(str(value).strip().upper(), format)
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return 24 * 60


def build_today_schedule(bookings):
    hours = {hour: [] for hour in range(10, 20)}
    other = []
    for booking in sorted(bookings, key=lambda item: (interview_time_minutes(item['start_time']), item['id'])):
        hour = interview_time_minutes(booking['start_time']) // 60
        if hour in hours:
            hours[hour].append(booking)
        else:
            other.append(booking)
    return [{'hour': hour, 'label': f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}", 'bookings': items} for hour, items in hours.items()], other


def get_todays_interviews():
    """Today's interviews in India time, ordered by actual start time."""
    conn = get_db_connection()
    try:
        bookings = conn.execute("""
            SELECT b.*, u.name as user_name, u.email as user_email,
                   s.interview_date, s.start_time, s.end_time, s.status as slot_status, l.name as license_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN interview_slots s ON b.slot_id = s.id
            JOIN licenses l ON s.license_id = l.id
            WHERE s.interview_date = DATE('now', '+5 hours', '+30 minutes')
        """).fetchall()
        return sorted([dict(booking) for booking in bookings], key=lambda item: (interview_time_minutes(item['start_time']), item['id']))
    finally:
        conn.close()


def reschedule_interview(booking_id, new_slot_id):
    import sqlite3

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Get the current booking with support_person
        cursor.execute(
            "SELECT slot_id, support_person FROM bookings WHERE id = ?",
            (booking_id,)
        )
        booking = cursor.fetchone()

        if not booking:
            conn.close()
            return False

        old_slot_id = booking["slot_id"]
        support_person = booking["support_person"]

        # Check whether the new slot is available
        cursor.execute(
            "SELECT * FROM interview_slots WHERE id = ? AND status = 'available'",
            (new_slot_id,)
        )
        slot = cursor.fetchone()

        if not slot:
            conn.close()
            return False

        # Update booking with the new slot, preserving support_person
        cursor.execute(
            "UPDATE bookings SET slot_id = ?, support_person = ? WHERE id = ?",
            (new_slot_id, support_person, booking_id)
        )

        # Make the old slot available
        cursor.execute(
            "UPDATE interview_slots SET status = 'available' WHERE id = ?",
            (old_slot_id,)
        )

        # Mark the new slot as booked
        cursor.execute(
            "UPDATE interview_slots SET status = 'booked' WHERE id = ?",
            (new_slot_id,)
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print("Reschedule Error:", e)
        conn.rollback()
        conn.close()
        return False

def reschedule_interview_by_time(booking_id, interview_date, start_time):
    import sqlite3

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')

        # Get the current booking with support_person
        cursor.execute(
            "SELECT slot_id, support_person FROM bookings WHERE id = ?",
            (booking_id,)
        )
        booking = cursor.fetchone()

        if not booking:
            conn.rollback()
            conn.close()
            return False

        old_slot_id = booking["slot_id"]
        support_person = booking["support_person"]

        # Check whether a new slot is available at the requested time
        cursor.execute('''
            SELECT id FROM interview_slots 
            WHERE interview_date = ? AND start_time = ? AND status = 'available'
            ORDER BY license_id ASC
            LIMIT 1
        ''', (interview_date, start_time))
        new_slot = cursor.fetchone()

        if not new_slot:
            conn.rollback()
            conn.close()
            return False
            
        new_slot_id = new_slot['id']

        # Update booking with the new slot, preserving support_person
        cursor.execute(
            "UPDATE bookings SET slot_id = ?, support_person = ? WHERE id = ?",
            (new_slot_id, support_person, booking_id)
        )

        # Make the old slot available
        cursor.execute(
            "UPDATE interview_slots SET status = 'available' WHERE id = ?",
            (old_slot_id,)
        )

        # Mark the new slot as booked
        cursor.execute(
            "UPDATE interview_slots SET status = 'booked' WHERE id = ?",
            (new_slot_id,)
        )

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print("Reschedule Error:", e)
        conn.rollback()
        conn.close()
        return False

def get_booking_by_id(booking_id):
    """Get booking by ID with all details."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.*, u.name AS user_name, u.email AS user_email,
               s.interview_date, s.start_time, s.end_time,
               s.status AS slot_status,
               l.name AS license_name
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN interview_slots s ON b.slot_id = s.id
        JOIN licenses l ON s.license_id = l.id
        WHERE b.id = ?
    """, (booking_id,))

    booking = cursor.fetchone()
    conn.close()

    if booking:
        return dict(booking)
    return None

def update_booking(booking_id, company_name, technology, interview_round, remarks):
    """Update booking details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE bookings SET company_name = ?, technology = ?, interview_round = ?, remarks = ? WHERE id = ?',
        (company_name, technology, interview_round, remarks, booking_id)
    )
    conn.commit()
    conn.close()

def cancel_booking(booking_id):
    """Cancel a booking and make the slot available again."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        # Get booking details
        cursor.execute('SELECT slot_id FROM bookings WHERE id = ?', (booking_id,))
        booking = cursor.fetchone()
        
        if not booking:
            conn.rollback()
            conn.close()
            return None
        
        slot_id = booking['slot_id']
        
        # Update booking status to cancelled
        cursor.execute('UPDATE bookings SET booking_status = ? WHERE id = ?', ('cancelled', booking_id))
        
        # Make slot available again
        cursor.execute('UPDATE interview_slots SET status = ? WHERE id = ?', ('available', slot_id))
        
        # Commit transaction
        conn.commit()
        conn.close()
        return booking_id
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return None

def initialize_default_licenses_and_slots():
    """Create default licenses and interview slots if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute('BEGIN TRANSACTION')
        
        # Check if Earth exists, create if not
        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Earth',))
        license1 = cursor.fetchone()
        if not license1:
            cursor.execute('INSERT INTO licenses (name, description) VALUES (?, ?)', ('Earth', 'Default interview license 1'))
            license1_id = cursor.lastrowid
        else:
            license1_id = license1['id']
        
        # Check if Moon exists, create if not
        cursor.execute('SELECT id FROM licenses WHERE name = ?', ('Moon',))
        license2 = cursor.fetchone()
        if not license2:
            cursor.execute('INSERT INTO licenses (name, description) VALUES (?, ?)', ('Moon', 'Default interview license 2'))
            license2_id = cursor.lastrowid
        else:
            license2_id = license2['id']
        
        # Define interview timings (same for both licenses)
        # 30-minute slots in professional format
        interview_timings = [
            ('2026-08-01', '09:00 AM', '10:00 AM'),
            ('2026-08-01', '10:00 AM', '11:00 AM'),
            ('2026-08-01', '11:00 AM', '12:00 PM'),
            ('2026-08-01', '12:00 PM', '01:00 PM'),
            ('2026-08-01', '01:00 PM', '02:00 PM'),
            ('2026-08-01', '02:00 PM', '03:00 PM'),
            ('2026-08-01', '03:00 PM', '04:00 PM'),
            ('2026-08-01', '04:00 PM', '05:00 PM'),
            ('2026-08-01', '05:00 pm', '06:00 pm'),
            ('2026-08-01', '06:00 PM', '07:00 PM'),
        ]
        
        # Create slots for License 1 if they don't exist
        for date, start, end in interview_timings:
            cursor.execute('''
                SELECT id FROM interview_slots 
                WHERE license_id = ? AND interview_date = ? AND start_time = ? AND end_time = ?
            ''', (license1_id, date, start, end))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (license1_id, date, start, end, 'available'))
        
        # Create slots for License 2 if they don't exist
        for date, start, end in interview_timings:
            cursor.execute('''
                SELECT id FROM interview_slots 
                WHERE license_id = ? AND interview_date = ? AND start_time = ? AND end_time = ?
            ''', (license2_id, date, start, end))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (license2_id, date, start, end, 'available'))
        
        # Commit transaction
        conn.commit()
        conn.close()
        
    except Exception as e:
        conn.rollback()
        conn.close()
        raise

def create_notification(user_id, notification_type, message):
    """Create a new notification for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO notifications (user_id, notification_type, message) VALUES (?, ?, ?)',
        (user_id, notification_type, message)
    )
    conn.commit()
    notification_id = cursor.lastrowid
    conn.close()
    return notification_id

def get_notifications(user_id, limit=None):
    """Get notifications for a user, ordered by creation date (newest first)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if limit:
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
    else:
        cursor.execute('''
            SELECT * FROM notifications 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
    
    notifications = cursor.fetchall()
    conn.close()
    
    return [dict(notification) for notification in notifications]

def mark_notification_read(notification_id):
    """Mark a notification as read."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
    conn.commit()
    conn.close()

def get_unread_notification_count(user_id):
    """Get count of unread notifications for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0', (user_id,))
    count = cursor.fetchone()['count']
    conn.close()
    
    return count

def get_dashboard_stats():
    """Get dashboard statistics for HR."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total slots
    cursor.execute('SELECT COUNT(*) as count FROM interview_slots')
    total_slots = cursor.fetchone()['count']
    
    # Available slots for today
    cursor.execute("SELECT COUNT(*) as count FROM interview_slots WHERE status = ? AND interview_date = DATE('now')", ('available',))
    available_slots = cursor.fetchone()['count']
    
    # Booked slots
    cursor.execute('SELECT COUNT(*) as count FROM interview_slots WHERE status = ?', ('booked',))
    booked_slots = cursor.fetchone()['count']
    
    # Cancelled bookings
    cursor.execute('SELECT COUNT(*) as count FROM bookings WHERE booking_status = ?', ('cancelled',))
    cancelled_bookings = cursor.fetchone()['count']
    
    # Today's interviews
    cursor.execute('''
        SELECT COUNT(*) as count 
        FROM bookings b 
        JOIN interview_slots s ON b.slot_id = s.id 
        WHERE b.booking_status = 'confirmed' 
        AND s.interview_date = DATE('now')
    ''')
    today_interviews = cursor.fetchone()['count']
    
    conn.close()
    
    return {
        'total_slots': total_slots,
        'available_slots': available_slots,
        'booked_slots': booked_slots,
        'cancelled_bookings': cancelled_bookings,
        'today_interviews': today_interviews
    }

def get_candidate_dashboard_stats(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # My booked slots
    cursor.execute(
        "SELECT COUNT(*) as count FROM bookings WHERE user_id = ? AND booking_status = ?",
        (user_id, "confirmed")
    )
    booked_slots = cursor.fetchone()["count"]

    # Upcoming interviews
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM bookings b
        JOIN interview_slots s ON b.slot_id = s.id
        WHERE b.user_id = ?
        AND b.booking_status = 'confirmed'
        AND s.interview_date >= DATE('now')
    """, (user_id,))
    upcoming_interviews = cursor.fetchone()["count"]

    # Temporary value until interview completion is implemented
    completed_interviews = 0

    # Cancelled interviews
    cursor.execute(
        "SELECT COUNT(*) as count FROM bookings WHERE user_id = ? AND booking_status = ?",
        (user_id, "cancelled")
    )
    cancelled_interviews = cursor.fetchone()["count"]

    conn.close()

    return {
        "booked_slots": booked_slots,
        "upcoming_interviews": upcoming_interviews,
        "completed_interviews": completed_interviews,
        "cancelled_interviews": cancelled_interviews
    }

def get_candidate_interview_history(user_id):
    """Get interview history for a candidate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.*, s.interview_date, s.start_time, s.end_time, l.name as license_name
        FROM bookings b 
        JOIN interview_slots s ON b.slot_id = s.id 
        JOIN licenses l ON s.license_id = l.id
        WHERE b.user_id = ?
        ORDER BY s.interview_date DESC, s.start_time DESC
    ''', (user_id,))
    
    history = cursor.fetchall()
    conn.close()
    
    return [dict(booking) for booking in history]

def complete_interview(booking_id, feedback, result):
    """Mark an interview as completed with feedback and result."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE bookings SET interview_completed = 1, interview_feedback = ?, interview_result = ? WHERE id = ?',
        (feedback, result, booking_id)
    )
    conn.commit()
    conn.close()

def assign_support_person(booking_id, support_person):
    """Assign a support person to a booking."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'UPDATE bookings SET support_person = ? WHERE id = ?',
        (support_person, booking_id)
    )
    conn.commit()
    conn.close()

def create_previous_interview_history(user_id, company_name, interview_round, interview_date, result, remarks=None):
    """Create a previous interview history entry for a candidate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO previous_interview_history (user_id, company_name, interview_round, interview_date, result, remarks) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, company_name, interview_round, interview_date, result, remarks)
    )
    conn.commit()
    history_id = cursor.lastrowid
    conn.close()
    return history_id

def get_previous_interview_history(user_id):
    """Get previous interview history for a candidate."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM previous_interview_history 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    
    history = cursor.fetchall()
    conn.close()
    
    return [dict(entry) for entry in history]

def create_default_hr_account():
    """Create a default HR account if one doesn't already exist."""
    import secrets
    
    # Check if any HR account exists
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('hr',))
    hr_count = cursor.fetchone()['count']
    
    if hr_count > 0:
        conn.close()
        return None
    
    # Use a predictable default password for demo deployments with ephemeral filesystems
    temp_password = "password123"
    
    # Create default HR account
    hashed_password = generate_password_hash(temp_password)
    
    try:
        cursor.execute(
            'INSERT INTO users (name, email, password, role, is_active, force_password_change) VALUES (?, ?, ?, ?, ?, ?)',
            ('HR Admin', 'hr@blujay.com', hashed_password, 'hr', 1, 1)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {'user_id': user_id, 'email': 'hr@blujay.com', 'temp_password': temp_password}
    except sqlite3.IntegrityError:
        conn.close()
        return None

def update_user_status(user_id, is_active):
    """Activate or deactivate a user account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (is_active, user_id))
    conn.commit()
    conn.close()

def reset_user_password(user_id, new_password):
    """Reset a user's password and force them to change it on next login."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash(new_password)
    
    cursor.execute(
        'UPDATE users SET password = ?, force_password_change = 1 WHERE id = ?',
        (hashed_password, user_id)
    )
    conn.commit()
    conn.close()

def change_user_password(user_id, new_password):
    """Change a user's password and mark as not requiring forced change."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    hashed_password = generate_password_hash(new_password)
    
    cursor.execute(
        'UPDATE users SET password = ?, force_password_change = 0 WHERE id = ?',
        (hashed_password, user_id)
    )
    conn.commit()
    conn.close()

def get_candidates():
    """Get all candidate users."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE role = ? ORDER BY id', ('candidate',))
    candidates = cursor.fetchall()
    conn.close()
    
    return [dict(candidate) for candidate in candidates]

def update_candidate(user_id, name, email):
    """Update candidate name and email."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            'UPDATE users SET name = ?, email = ? WHERE id = ?',
            (name, email, user_id)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

if __name__ == '__main__':
    create_tables()


def delete_candidate_account(user_id):
    """Atomically remove a candidate and their records, freeing confirmed slots."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute('BEGIN IMMEDIATE')
            candidate = conn.execute("SELECT id FROM users WHERE id = ? AND role = 'candidate'", (user_id,)).fetchone()
            if not candidate:
                return False
            slots = conn.execute("SELECT DISTINCT slot_id FROM bookings WHERE user_id = ? AND booking_status = 'confirmed'", (user_id,)).fetchall()
            for table in ('notifications', 'previous_interview_history', 'user_preferences', 'bookings'):
                conn.execute(f'DELETE FROM {table} WHERE user_id = ?', (user_id,))
            for slot in slots:
                conn.execute("UPDATE interview_slots SET status = 'available' WHERE id = ? AND status = 'booked' AND NOT EXISTS (SELECT 1 FROM bookings WHERE slot_id = ? AND booking_status = 'confirmed')", (slot['slot_id'], slot['slot_id']))
            conn.execute("DELETE FROM users WHERE id = ? AND role = 'candidate'", (user_id,))
        return True
    finally:
        conn.close()

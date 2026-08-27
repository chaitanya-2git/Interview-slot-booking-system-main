import sqlite3

# Get user credentials
conn = sqlite3.connect('interview_booking.db')
cursor = conn.cursor()
cursor.execute('SELECT email FROM users WHERE role="candidate" LIMIT 1')
user = cursor.fetchone()
conn.close()

if user:
    print(f"Test user email: {user[0]}")
    print("Please login with this user and check the browser's generated HTML for:")
    print("1. bookingModal82, bookingModal83 (first two available slot IDs)")
    print("2. data-bs-target attributes matching these modal IDs")
    print("3. Modal divs present in the HTML")
else:
    print("No candidate users found")

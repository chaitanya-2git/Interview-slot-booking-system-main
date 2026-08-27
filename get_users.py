import sqlite3

conn = sqlite3.connect('interview_booking.db')
cursor = conn.cursor()
cursor.execute('SELECT id, name, email, role FROM users WHERE role="candidate"')
users = cursor.fetchall()
print('Candidate users in database:')
for u in users:
    print(f'ID: {u[0]}, Name: {u[1]}, Email: {u[2]}, Role: {u[3]}')
conn.close()

import sqlite3

conn = sqlite3.connect('interview_booking.db')
cursor = conn.cursor()
cursor.execute('SELECT id FROM interview_slots WHERE status="available" ORDER BY id LIMIT 5')
rows = cursor.fetchall()
print('Available slot IDs:')
for r in rows:
    print(f'ID: {r[0]}')
conn.close()

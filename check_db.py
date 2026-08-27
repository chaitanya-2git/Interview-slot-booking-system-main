import sqlite3

conn = sqlite3.connect("interview_booking.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM interview_slots")
print("Total Slots:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM interview_slots WHERE status='available'")
print("Available Slots:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM interview_slots WHERE status='booked'")
print("Booked Slots:", cursor.fetchone()[0])

conn.close()
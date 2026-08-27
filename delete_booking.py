import sqlite3

conn = sqlite3.connect("interview_booking.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM bookings WHERE id = 1")

conn.commit()
conn.close()

print("Booking deleted successfully!")
import sqlite3
import database

c = sqlite3.connect(database.DATABASE)

c.execute("UPDATE interview_slots SET status = ?", ("available",))

c.commit()

print("All interview slots reset to available")

print("Bookings:", c.execute("SELECT COUNT(*) FROM bookings").fetchone()[0])

print("Booked slots:", c.execute("SELECT COUNT(*) FROM interview_slots WHERE status = ?", ("booked",)).fetchone()[0])

print("Available slots:", c.execute("SELECT COUNT(*) FROM interview_slots WHERE status = ?", ("available",)).fetchone()[0])

print("Total slots:", c.execute("SELECT COUNT(*) FROM interview_slots").fetchone()[0])

c.close()

import sqlite3

conn = sqlite3.connect("interview_booking.db")
cursor = conn.cursor()

# Keep only the first 20 slots
cursor.execute("""
DELETE FROM interview_slots
WHERE id NOT IN (
    SELECT id
    FROM interview_slots
    ORDER BY id
    LIMIT 20
)
""")

conn.commit()

cursor.execute("SELECT COUNT(*) FROM interview_slots")
print("Remaining slots:", cursor.fetchone()[0])

conn.close()
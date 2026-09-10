import os
import tempfile
import database
from app import app

original = database.DATABASE
with tempfile.TemporaryDirectory() as directory:
    try:
        database.DATABASE = os.path.join(directory, 'delete.db')
        database.create_tables()
        hr = database.register_user('HR', 'hr@test.com', 'Password123!', 'hr', force_password_change=0)
        candidate = database.register_user('Candidate', 'candidate@test.com', 'Password123!', 'candidate', force_password_change=0)
        conn = database.get_db_connection()
        with conn:
            conn.execute("INSERT INTO licenses (name) VALUES ('Test')")
            conn.execute("INSERT INTO interview_slots (license_id, interview_date, start_time, end_time, status) VALUES (1, '2030-01-01', '10:00 AM', '11:00 AM', 'booked')")
            conn.execute("INSERT INTO bookings (user_id, slot_id, booking_status) VALUES (?, 1, 'confirmed')", (candidate,))
            conn.execute("INSERT INTO notifications (user_id, notification_type, message) VALUES (?, 'info', 'Test')", (candidate,))
            conn.execute("INSERT INTO user_preferences (user_id) VALUES (?)", (candidate,))
            conn.execute("INSERT INTO previous_interview_history (user_id,company_name,interview_round,interview_date,result) VALUES (?, 'Test', 'L1', '2030-01-01', 'Passed')", (candidate,))
        conn.close()
        app.config['TESTING'] = True
        client = app.test_client()
        victim = app.test_client()
        victim.post('/login', data={'email':'candidate@test.com','password':'Password123!'})
        assert victim.post(f'/delete-candidate/{candidate}').status_code == 403
        assert client.post(f'/delete-candidate/{candidate}').status_code == 403
        client.post('/login', data={'email':'hr@test.com','password':'Password123!'})
        assert client.get(f'/delete-candidate/{candidate}').status_code == 200
        assert database.get_user_by_id(candidate)
        with client.session_transaction() as session:
            token = session['delete_candidate_csrf']
        assert client.post(f'/delete-candidate/{candidate}', data={'confirmation':'candidate@test.com'}).status_code == 400
        assert b'exactly' in client.post(f'/delete-candidate/{candidate}', data={'csrf_token':token,'confirmation':'wrong@test.com'}).data
        assert client.post(f'/delete-candidate/{hr}', data={'csrf_token':token,'confirmation':'hr@test.com'}).status_code == 404
        assert client.post(f'/delete-candidate/{candidate}', data={'csrf_token':token,'confirmation':'candidate@test.com'}).status_code == 302
        assert not database.get_user_by_id(candidate)
        conn = database.get_db_connection()
        for table in ['bookings','notifications','user_preferences','previous_interview_history']:
            assert conn.execute(f'SELECT count(*) FROM {table} WHERE user_id=?',(candidate,)).fetchone()[0] == 0
        assert conn.execute('SELECT status FROM interview_slots WHERE id=1').fetchone()[0] == 'available'
        conn.close()
        assert victim.get('/candidate-dashboard').status_code == 302
        assert client.get(f'/delete-candidate/{candidate}').status_code == 404
        print('Deletion passed: permissions, confirmation, CSRF, HR protection, related cleanup, slot release, stale session rejection.')
    finally:
        database.DATABASE = original

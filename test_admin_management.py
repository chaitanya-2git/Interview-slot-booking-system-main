"""Admin role and account creation integration checks in an isolated database."""
import os
import tempfile
import database
from app import app

original = database.DATABASE
with tempfile.TemporaryDirectory() as directory:
    try:
        database.DATABASE = os.path.join(directory, 'admins.db')
        database.create_tables()
        admin_id = database.register_user('Admin', 'admin@test.com', 'Admin123!', 'admin', force_password_change=0)
        database.register_user('HR', 'hr@test.com', 'HrPassword123!', 'hr', force_password_change=0)
        database.register_user('Candidate', 'candidate@test.com', 'Candidate123!', 'candidate', force_password_change=0)
        app.config['TESTING'] = True
        client = app.test_client()
        assert client.get('/manage-admins').status_code == 403
        for email, password in [('hr@test.com','HrPassword123!'),('candidate@test.com','Candidate123!')]:
            client.post('/login', data={'email':email,'password':password})
            assert client.get('/manage-admins').status_code == 403
            assert client.post('/manage-admins',data={'name':'Unauthorized','email':'bad@test.com','password':'Password123!'}).status_code == 403
            client.get('/logout')
        response = client.post('/login', data={'email':'admin@test.com','password':'Admin123!'})
        assert response.location.endswith('/hr-dashboard')
        for url in ['/hr-dashboard','manage-candidates','create-candidate','settings','manage-admins']:
            assert client.get('/'+url.lstrip('/')).status_code == 200, url
        assert b'Manage Admins' in client.get('/hr-dashboard').data
        with client.session_transaction() as session:
            token = session['admin_csrf']
        data = {'name':'Second Admin','email':'second@test.com','password':'Second123!','confirm_password':'Second123!'}
        assert client.post('/manage-admins', data=data).status_code == 400
        data['csrf_token'] = token
        assert client.post('/manage-admins',data={**data,'confirm_password':'wrong'}).status_code == 200
        assert client.post('/manage-admins', data=data).status_code == 302
        assert b'already in use' in client.post('/manage-admins', data=data).data
        user = database.login_user('second@test.com','Second123!')
        assert user['role'] == 'admin' and user['force_password_change'] == 1
        client.get('/logout')
        response = client.post('/login',data={'email':'second@test.com','password':'Second123!'})
        assert response.location.endswith('/change-password')
        assert client.get('/manage-admins').location.endswith('/change-password')
        response = client.post('/change-password',data={'new_password':'Second456!','confirm_password':'Second456!'})
        assert response.location.endswith('/hr-dashboard')
        assert client.get('/manage-admins').status_code == 200
        assert client.post('/create-candidate',data={'name':'Admin Candidate','email':'newcandidate@test.com','password':'Candidate123!'}).status_code == 302
        candidate = database.login_user('newcandidate@test.com','Candidate123!')
        assert candidate and candidate['role'] == 'candidate'
        assert client.get(f"/delete-candidate/{candidate['id']}").status_code == 200
        print('Admin tests passed: role isolation, dashboard, candidate management, CSRF, validation, admin creation, forced password change.')
    finally:
        database.DATABASE = original

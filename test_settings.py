"""Settings integration checks against an isolated database."""
import os
import tempfile
import database
from app import app


def main():
    original = database.DATABASE
    with tempfile.TemporaryDirectory() as directory:
        database.DATABASE = os.path.join(directory, 'settings.db')
        try:
            database.create_tables()
            uid = database.register_user('Settings User', 'settings@example.com', 'Original123!', 'hr', force_password_change=0)
            other = database.register_user('Other', 'other@example.com', 'Other123!', 'candidate', force_password_change=0)
            app.config['TESTING'] = True
            client = app.test_client()
            assert client.get('/settings').status_code == 302
            client.post('/login', data={'email': 'settings@example.com', 'password': 'Original123!'})
            assert client.get('/settings').status_code == 200
            with client.session_transaction() as session:
                token = session['settings_csrf']
            def post(**data):
                return client.post('/settings', data={'csrf_token': token, **data})
            assert client.post('/settings', data={'action': 'profile'}).status_code == 400
            assert post(action='profile', name='Updated Name', email='settings@example.com').status_code == 302
            assert database.get_user_by_id(uid)['name'] == 'Updated Name'
            assert b'current password' in post(action='profile', name='Updated Name', email='new@example.com').data
            assert b'already in use' in post(action='profile', name='Updated Name', email='OTHER@example.com', current_password='Original123!').data
            assert post(action='profile', name='Updated Name', email='new@example.com', current_password='Original123!').status_code == 302
            assert b'incorrect' in post(action='password', current_password='wrong', new_password='Changed123!', confirm_password='Changed123!').data
            assert b'at least 8' in post(action='password', current_password='Original123!', new_password='short', confirm_password='short').data
            assert b'do not match' in post(action='password', current_password='Original123!', new_password='Changed123!', confirm_password='different').data
            assert post(action='password', current_password='Original123!', new_password='Changed123!', confirm_password='Changed123!').status_code == 302
            assert database.login_user('new@example.com', 'Changed123!')
            assert not database.login_user('new@example.com', 'Original123!')
            assert post(action='preferences', larger_text='on', reduce_motion='on').status_code == 302
            html = client.get('/settings').data
            assert b'pref-larger-text pref-reduce-motion' in html
            assert database.get_user_by_id(other)['email'] == 'other@example.com'
            client.get('/logout')
            client.post('/login', data={'email': 'new@example.com', 'password': 'Changed123!'})
            assert b'pref-larger-text pref-reduce-motion' in client.get('/settings').data
            with client.session_transaction() as session:
                token = session['settings_csrf']
            assert post(action='preferences').status_code == 302
            assert b'<body class="">' in client.get('/settings').data
            client.get('/logout')
            client.post('/login', data={'email': 'other@example.com', 'password': 'Other123!'})
            assert client.get('/settings').status_code == 200
            assert b'<body class="">' in client.get('/settings').data
            print('Settings passed: access, CSRF, profile/email validation, password changes, persistent preferences, account isolation, HR and candidate access.')
        finally:
            database.DATABASE = original


if __name__ == '__main__':
    main()

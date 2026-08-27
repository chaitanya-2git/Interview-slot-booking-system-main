from flask import Flask, render_template, request, redirect, url_for, session, flash
from simple_database import create_tables, register_user, login_user, get_user_by_id

app = Flask(__name__)
app.secret_key = "simple-secret-key"

create_tables()

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = login_user(email, password)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')

    return render_template('simple_login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        user_id = register_user(name, email, password)
        if user_id:
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

        flash('Email already registered. Please use a different email.', 'danger')

    return render_template('simple_register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = get_user_by_id(session['user_id'])
    return render_template('simple_dashboard.html', user=user)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

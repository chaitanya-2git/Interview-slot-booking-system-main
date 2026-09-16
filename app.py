import os
from flask import Flask
from routes import app_routes
from database import create_tables, initialize_default_licenses_and_slots, create_default_hr_account

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8 MB resume upload limit
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")

# Create the database tables
create_tables()

# Initialize default licenses and slots
initialize_default_licenses_and_slots()

# Create default HR account if one doesn't exist
default_hr = create_default_hr_account()
if default_hr:
    print("=" * 60)
    print("DEFAULT HR ACCOUNT CREATED")
    print("=" * 60)
    print(f"Email: {default_hr['email']}")
    print(f"Password: {default_hr['password']}")
    print("=" * 60)

# Register routes
app.register_blueprint(app_routes)


@app.errorhandler(413)
def resume_file_too_large(_error):
    from flask import flash, redirect, request, url_for
    flash('Resume file is too large. Upload a file smaller than 8 MB.', 'error')
    return redirect(request.referrer or url_for('main.candidate_profile'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

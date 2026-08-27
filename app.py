from flask import Flask
from routes import app_routes
from database import create_tables, initialize_default_licenses_and_slots, create_default_hr_account

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

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
    print(f"Temporary Password: {default_hr['temp_password']}")
    print("Please change this password after first login.")
    print("=" * 60)

# Register routes
app.register_blueprint(app_routes)

if __name__ == "__main__":
    app.run(debug=True)
    
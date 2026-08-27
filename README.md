# ?? BluJay Technologies — Interview Slot Booking System

> **A full-featured web application for streamlining interview scheduling between HR teams and candidates.**

Built with **Python Flask**, **SQLite**, **Bootstrap 5**, and vanilla **JavaScript** — this system provides a dual-role interface for HR staff and candidates to efficiently manage interview appointments.

---

## ?? Features

### ?? HR Panel
| Feature | Description |
|---|---|
| **Dashboard** | Overview stats — total bookings, available slots, today's interviews, total candidates |
| **Manage Bookings** | View, edit, cancel, and reschedule all candidate bookings |
| **Today's Interviews** | Dedicated view for interviews scheduled for the current day |
| **Create Interview Slots** | Create time slots per license type (Earth / Moon) |
| **Edit / Delete Slots** | Modify or remove existing interview time slots |
| **Manage Candidates** | Create, edit, activate/deactivate candidate accounts |
| **Create Candidate Slot** | Book an extra interview slot for a specific candidate (overrides booking limits) |
| **Complete Interview** | Mark an interview as done, record feedback and result |
| **Assign Support Person** | Assign a support personnel name to any booking |
| **Candidate History** | View full interview history for any candidate |
| **Reschedule Interviews** | Reassign a candidate to a different available slot |
| **Notifications** | Real-time notification system for all booking events |
| **Reports** | Analytics and statistics view |
| **Reset Candidate Password** | Generate a new temporary password for a candidate |

### ?? Candidate Panel
| Feature | Description |
|---|---|
| **Dashboard** | Overview of personal stats — total, upcoming, completed, cancelled bookings |
| **Book Interview Slot** | Pick a date ? select license type (Earth/Moon) ? choose a time slot ? fill booking details |
| **My Bookings** | View all upcoming and past bookings with status |
| **Change Slot** | Reschedule an existing booking to a different available slot |
| **Cancel Booking** | Cancel a confirmed interview booking |
| **Previous Interview History** | Log and view externally attended interviews (pre-registration) |
| **Notifications** | Receive real-time alerts for booking confirmations, reschedules, and results |
| **Change Password** | Update account password (forced on first login) |

---

## ??? Project Structure

```
Interview-slot-booking-system-main/
¦
+-- app.py                    # Flask app entry point — initializes DB, registers routes
+-- routes.py                 # All route/view definitions (Blueprint)
+-- database.py               # SQLite database layer — all CRUD operations
+-- requirements.txt          # Python dependencies
¦
+-- templates/                # Jinja2 HTML templates
¦   +-- base.html             # Base layout with sidebar and navigation
¦   +-- index.html            # Login / landing page
¦   +-- login.html            # Alternate login page
¦   +-- hr_dashboard.html     # Full HR dashboard
¦   +-- candidate_dashboard.html  # Full candidate dashboard
¦   +-- candidate_history.html    # HR view of a candidate's interview history
¦   +-- create_slot.html          # Form to create a new interview slot
¦   +-- edit_slot.html            # Form to edit an existing slot
¦   +-- create_candidate.html     # Form for HR to add a new candidate
¦   +-- edit_candidate.html       # Form to edit candidate details
¦   +-- manage_candidates.html    # List of all candidates with actions
¦   +-- create_candidate_slot.html # Book extra slot for a candidate (HR)
¦   +-- edit_booking.html         # Edit booking details
¦   +-- complete_interview.html   # Mark interview as complete + record feedback
¦   +-- reschedule_interview.html       # Full reschedule page
¦   +-- reschedule_interview_partial.html # Modal partial for AJAX reschedule
¦   +-- change_slot_partial.html  # Modal partial for candidate slot change
¦   +-- change_password.html      # Password change page
¦   +-- reset_candidate_password.html   # HR resets a candidate password
¦
+-- static/
¦   +-- css/
¦   ¦   +-- style.css         # Global stylesheet
¦   +-- js/
¦   ¦   +-- script.js         # Frontend interactivity (AJAX, modals, UI)
¦   +-- images/
¦       +-- blujay_logo.jpg   # Company branding logo
¦
+-- check_db.py               # Utility: inspect database state
+-- check_slots.py            # Utility: check available slots
+-- delete_booking.py         # Utility: manually delete a booking
+-- get_users.py              # Utility: list all users
+-- reduce_slots.py           # Utility: reduce slot count
+-- reset_database.py         # Utility: wipe and reinitialize database
+-- test_dashboard.py         # Dashboard testing script
+-- verify_html.py            # HTML template verification script
```

---

## ??? Database Schema

The application uses **SQLite** (`interview_booking.db`) with the following tables:

```
+--------------------------------------------------+
¦ users                                            ¦
+--------------------------------------------------¦
¦ id, name, email, password (hashed), role,        ¦
¦ is_active, force_password_change                 ¦
+--------------------------------------------------+

+--------------------------------------------------+
¦ licenses                                         ¦
+--------------------------------------------------¦
¦ id, name (Earth / Moon), description             ¦
+--------------------------------------------------+

+--------------------------------------------------+
¦ interview_slots                                  ¦
+--------------------------------------------------¦
¦ id, license_id (FK), interview_date,             ¦
¦ start_time, end_time, status (available/booked)  ¦
+--------------------------------------------------+

+--------------------------------------------------+
¦ bookings                                         ¦
+--------------------------------------------------¦
¦ id, user_id (FK), slot_id (FK),                  ¦
¦ booking_status, company_name, technology,        ¦
¦ interview_round, remarks, interview_feedback,    ¦
¦ interview_result, interview_completed,           ¦
¦ support_person                                   ¦
+--------------------------------------------------+

+--------------------------------------------------+
¦ notifications                                    ¦
+--------------------------------------------------¦
¦ id, user_id (FK), notification_type, message,    ¦
¦ is_read, created_at                              ¦
+--------------------------------------------------+

+--------------------------------------------------+
¦ previous_interview_history                       ¦
+--------------------------------------------------¦
¦ id, user_id (FK), company_name, interview_round, ¦
¦ interview_date, result, remarks, created_at      ¦
+--------------------------------------------------+
```

---

## ?? Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3, Flask 3.0.0 |
| **Database** | SQLite (via `sqlite3`) |
| **Auth** | Werkzeug password hashing |
| **Frontend** | HTML5, Bootstrap 5.3, Bootstrap Icons |
| **Styling** | Vanilla CSS (`static/css/style.css`) |
| **JavaScript** | Vanilla JS with AJAX for dynamic slot loading |
| **Templating** | Jinja2 (Flask built-in) |

---

## ?? Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Interview-slot-booking-system.git
cd Interview-slot-booking-system-main
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The app will start at **http://127.0.0.1:5000**

---

## ?? Default Credentials

On **first startup**, the application automatically:
1. Creates all database tables
2. Initializes two default licenses: **Earth** and **Moon**
3. Creates a **default HR account** and prints credentials to the console

```
============================================================
DEFAULT HR ACCOUNT CREATED
============================================================
Email: <auto-generated>
Temporary Password: <auto-generated>
Please change this password after first login.
============================================================
```

> ?? **Important:** Change the default HR password immediately after the first login.

---

## ?? User Roles

### `hr` — Human Resources
- Full administrative access
- Can create, edit, delete slots and candidates
- Can view and manage all bookings
- Can complete interviews and record results

### `candidate` — Interview Candidate
- Accounts created **only by HR** (public registration is disabled)
- Can book available interview slots
- Can reschedule or cancel own bookings
- Can log previous interview history
- Forced to change password on first login

---

## ?? API Endpoints (Routes Reference)

| Method | Route | Role | Description |
|---|---|---|---|
| `GET/POST` | `/` | All | Login page |
| `GET/POST` | `/login` | All | Alternate login |
| `GET` | `/logout` | All | Logout and clear session |
| `GET/POST` | `/change-password` | All | Change own password |
| `GET` | `/hr-dashboard` | HR | HR main dashboard |
| `GET` | `/todays-interviews` | HR | Today's scheduled interviews |
| `GET` | `/candidate-dashboard` | Candidate | Candidate main dashboard |
| `GET` | `/available-slots-by-date` | Candidate | AJAX: fetch slots for a date |
| `POST` | `/book-slot/<slot_id>` | Candidate | Book an interview slot |
| `GET/POST` | `/create-slot` | HR | Create a new interview slot |
| `GET/POST` | `/edit-slot/<slot_id>` | HR | Edit an existing slot |
| `POST` | `/delete-slot/<slot_id>` | HR | Delete a slot |
| `GET/POST` | `/reschedule/<booking_id>` | HR | Reschedule (AJAX + full page) |
| `GET/POST` | `/candidate-change-slot/<booking_id>` | Candidate | Change own booking slot |
| `GET/POST` | `/edit-booking/<booking_id>` | HR | Edit booking details |
| `POST` | `/cancel-booking/<booking_id>` | HR | Cancel a booking (HR) |
| `POST` | `/candidate-cancel-booking/<booking_id>` | Candidate | Cancel own booking |
| `GET/POST` | `/complete-interview/<booking_id>` | HR | Mark interview complete + record result |
| `POST` | `/assign-support/<booking_id>` | HR | Assign support person to booking |
| `GET` | `/candidate-history/<user_id>` | HR | View a candidate full history |
| `GET` | `/manage-candidates` | HR | List all candidates |
| `GET/POST` | `/create-candidate` | HR | Create new candidate account |
| `GET/POST` | `/edit-candidate/<user_id>` | HR | Edit candidate profile |
| `POST` | `/toggle-candidate-status/<user_id>` | HR | Activate/deactivate candidate |
| `POST` | `/reset-candidate-password/<user_id>` | HR | Reset candidate password |
| `GET/POST` | `/create-candidate-slot/<user_id>` | HR | Book extra slot for candidate |
| `POST` | `/add-previous-history` | Candidate | Log previous interview record |
| `POST` | `/get-slots-by-date` | HR | AJAX: generate/fetch slots for date |
| `POST` | `/mark-notification-read/<id>` | All | Mark notification as read |

---

## ?? Notification System

The system sends in-app notifications for key events:

| Event | Notified Parties |
|---|---|
| Slot booked by candidate | Candidate + All HR |
| Booking cancelled (by HR) | Candidate |
| Booking cancelled (by candidate) | All HR |
| Slot changed by candidate | All HR |
| Interview rescheduled (by HR) | Candidate |
| Interview completed | Candidate |
| Result available | Candidate |
| Max bookings limit reached | All HR |

---

## ?? Utility Scripts

| Script | Purpose |
|---|---|
| `check_db.py` | Inspect the current state of the database |
| `check_slots.py` | Check available interview slots |
| `delete_booking.py` | Manually delete a specific booking |
| `get_users.py` | List all registered users |
| `reduce_slots.py` | Reduce number of available slots |
| `reset_database.py` | ?? Wipe and reinitialize the entire database |
| `verify_html.py` | Verify that all HTML templates are valid |
| `test_dashboard.py` | Test dashboard functionality |

---

## ?? Security Features

- Passwords stored using **Werkzeug PBKDF2-SHA256** hashing — never plain text
- Session-based authentication with Flask sessions
- **Role-based access control (RBAC)** on every route
- Candidates can only access/modify their **own** bookings
- **Force password change** on first login for newly created accounts
- Public registration is **disabled** — only HR can create candidate accounts
- Inactive accounts are blocked from logging in

---

## ??? Configuration

Open `app.py` to configure the secret key:

```python
app.secret_key = "your-secret-key-here"  # Change this in production!
```

> ?? **Production Note:** Use a strong, randomly generated secret key stored as an environment variable.

```python
import os
app.secret_key = os.environ.get("SECRET_KEY", "fallback-dev-key")
```

---

## ?? Responsive Design

The UI is built with **Bootstrap 5.3** and is fully responsive across:
- ??? Desktop (1200px+)
- ?? Laptop (992px+)
- ?? Mobile (< 768px)

---

## ?? Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

## ?? License

This project is proprietary to **BluJay Technologies**. All rights reserved.

---

## ?? Authors

**BluJay Technologies Development Team**

> *Innovating the Future of Technology*

---

<p align="center">
  <strong>BluJay Technologies © 2024 — Interview Slot Booking System</strong>
</p>

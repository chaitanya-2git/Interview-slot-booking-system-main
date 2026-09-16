# BluJay Interview Portal

A role-based interview scheduling and candidate-management portal for BluJay Technologies. Candidates can maintain professional profiles, upload resumes, book interview slots, and track their interviews. HR and administrators manage candidates, schedules, interview results, and talent discovery from one workspace.

## Contents

- [What the application does](#what-the-application-does)
- [Roles and permissions](#roles-and-permissions)
- [Key features](#key-features)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Run locally](#run-locally)
- [Configuration](#configuration)
- [Testing](#testing)
- [Production deployment](#production-deployment)
- [Data and uploads](#data-and-uploads)
- [Security notes](#security-notes)

## What the application does

The portal centralizes the interview process from candidate onboarding through booking, rescheduling, completion, and feedback.

Candidates can choose an available interview time, enter booking information, change or cancel a booking, receive in-app notifications, and view their interview history. They can also create a professional profile with skills, experience, education, notice period, LinkedIn URL, resume, and profile photo.

HR and administrators can create slots, manage bookings, review candidate profiles and resumes, search talent by skill and experience, and record interview outcomes.

## Roles and permissions

| Role | Access |
| --- | --- |
| Candidate | Own dashboard, profile, resume/photo upload, available slots, bookings, rescheduling, cancellation, notifications, history, and settings. |
| HR | Candidate management, Talent Search, slots, bookings, today’s schedule, support assignments, feedback, and interview results. |
| Admin | All HR permissions plus administrator-account management. |

## Key features

### Candidate experience

- Secure sign-in with password hashing and forced password changes for new accounts.
- Responsive dashboard for desktop and mobile.
- Available slots are filtered so time slots that have already started today are not bookable.
- Book an interview with company, technology, interview round, remarks, and HR contact details.
- Change an existing slot or cancel a confirmed booking.
- View upcoming, completed, cancelled, and previous interviews.
- Receive in-app booking, reschedule, cancellation, and result notifications.
- Professional profile onboarding wizard.
- Resume upload for PDF, DOC, and DOCX files.
- Resume parsing for PDF and DOCX files, with extracted phone, experience, skills, and education available for review before saving.
- Profile photo upload using JPG, JPEG, PNG, or WEBP formats, up to 2 MB.
- Private resume download and private profile-photo delivery for authorized users.

### HR and administrator operations

- Dashboard metrics for bookings, candidates, available slots, and interviews.
- Today’s interviews shown in chronological time order.
- Create, edit, and delete interview slots.
- Manage booking details, reschedules, cancellations, support-person assignments, feedback, and interview results.
- Create candidates, update accounts, activate/deactivate access, reset passwords, and delete candidates.
- Review complete candidate profiles, booking history, skills, education, and uploaded resumes.
- Download candidate resumes from management, Talent Search, and candidate-details pages.
- Single-field Talent Search for skill and minimum experience.
  - `Python` finds candidates with Python in their saved skills.
  - `DevOps 5+ years` finds candidates with DevOps and at least five years of experience.
  - `React 2 years` finds candidates with React and at least two years of experience.
- Add and manage additional administrator accounts.

## Technology stack

| Area | Technology |
| --- | --- |
| Backend | Python 3, Flask 3 |
| Production WSGI server | Gunicorn |
| Database | SQLite through Python `sqlite3` |
| Authentication | Flask sessions and Werkzeug password hashing |
| Templates | Jinja2 |
| Frontend | HTML5, CSS3, JavaScript, Bootstrap Icons |
| Resume parsing | `pypdf`, `python-docx` |
| Browser testing | Playwright |
| Deployment target | Oracle Cloud Ubuntu VM, Nginx, Gunicorn, Cloudflare DNS |

## Architecture

```text
Browser
  |
  v
Nginx + HTTPS (production)
  |
  v
Gunicorn
  |
  v
Flask application
  |-- routes.py             Request handling and role checks
  |-- templates/            Jinja pages
  |-- static/               CSS, JavaScript, branding assets
  |-- database.py           SQLite schema, migrations, and queries
  |-- uploads/resumes/      Private resume files
  `-- uploads/photos/       Private candidate photos
```

## Project structure

```text
.
├── app.py                  Flask application entry point
├── routes.py               Application routes and business workflows
├── database.py             SQLite schema, migrations, and database helpers
├── resume_parser.py        PDF and DOCX resume extraction
├── requirements.txt        Python dependencies
├── templates/              Jinja HTML pages
├── static/
│   ├── css/                Application, login, profile, and details styles
│   ├── js/                 Client-side interactions
│   └── images/             BluJay assets
├── uploads/
│   ├── resumes/            Private uploaded resumes, ignored by Git
│   └── photos/             Private uploaded profile photos, ignored by Git
├── e2e/
│   ├── tests/              Playwright end-to-end tests
│   └── server.py           Disposable test server and test database setup
├── playwright.config.js    Playwright configuration
└── package.json            E2E test commands
```

## Run locally

### Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer for Playwright tests
- Git

### Setup

```bash
git clone https://github.com/chaitanya-2git/Interview-slot-booking-system-main.git
cd Interview-slot-booking-system-main

# Windows
py -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in a browser.

The application creates the SQLite database and required tables automatically on first run.

## Configuration

Set the following environment variables for production:

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | Yes | Securely signs session cookies. Use a long random value. |
| `PORT` | No | Port used by Flask locally. Defaults to `5000`. |

PowerShell example:

```powershell
$env:SECRET_KEY = "replace-with-a-long-random-secret"
python app.py
```

Never use the development fallback secret in production.

## Testing

The project uses Playwright for end-to-end browser tests. Playwright starts a disposable Flask server and a temporary SQLite database, so tests do not alter your local `interview_booking.db`.

Install JavaScript dependencies:

```bash
npm install
```

Run tests:

```bash
npm run test:e2e
npm run test:e2e:ui
npm run test:e2e:headed
```

Current E2E coverage includes:

- HR and candidate authentication.
- Candidate onboarding with resume parsing.
- Candidate profile photo upload and display.
- Slot loading, interview booking, and cancellation.
- HR Talent Search by skill and minimum experience.

HTML reports are written to `playwright-report/`. Screenshots and traces are retained for failed tests in `test-results/`.

## Production deployment

### Recommended always-on deployment

For an always-on deployment without Render’s free-service sleep behavior, use this architecture:

```text
interviews.blujaytech.com
        |
Cloudflare DNS
        |
Oracle Cloud Ubuntu VM
  ├── Nginx
  ├── Gunicorn
  ├── Flask
  ├── SQLite initially
  └── PostgreSQL later for higher usage
```

Hostinger Web Hosting cannot run this application because it is a Python/Flask server application. It can continue to host `www.blujaytech.com`, while `interviews.blujaytech.com` points through Cloudflare to the Oracle VM.

Production setup checklist:

1. Create an Ubuntu VM in Oracle Cloud.
2. Open inbound ports 80 and 443. Restrict SSH port 22 to trusted access where possible.
3. Clone this repository to the VM.
4. Create a Python virtual environment and install `requirements.txt`.
5. Run the application with Gunicorn, for example: `gunicorn --workers 1 --bind 127.0.0.1:8000 app:app`.
6. Configure Nginx to proxy `interviews.blujaytech.com` to Gunicorn.
7. Issue an SSL certificate and configure Cloudflare SSL mode to **Full (strict)**.
8. Create a `systemd` service so Gunicorn starts automatically after a server restart.
9. Set `SECRET_KEY` as a protected environment variable.
10. Back up the database and upload directories daily.

### Database recommendation

SQLite is suitable for local development and a small initial deployment. When multiple HR users and candidates use the application concurrently, migrate to PostgreSQL for stronger concurrency, reliability, managed backups, and safer schema changes.

## Data and uploads

- Main database: `interview_booking.db`
- Resumes: `uploads/resumes/`
- Candidate photos: `uploads/photos/`

The upload folders and local databases are excluded from Git by `.gitignore`. They must be included in server backups.

## Security notes

- Passwords are stored as hashes, never plain text.
- Resumes and candidate photos are served through authenticated routes rather than public static URLs.
- Only a candidate owner, HR, or an administrator can access candidate documents.
- File extensions and upload sizes are restricted.
- Use HTTPS, a strong `SECRET_KEY`, regular backups, and unique production passwords before public use.
- Use one Gunicorn worker while the application uses SQLite to avoid unnecessary concurrent-write contention.

## License

This project is private and intended for BluJay Technologies internal interview operations.

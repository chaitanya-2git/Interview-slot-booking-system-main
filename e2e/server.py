"""Run the Flask application with a disposable E2E database."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DATABASE_PATH = ROOT / "e2e" / ".tmp" / "playwright-e2e.db"
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
if DATABASE_PATH.exists():
    DATABASE_PATH.unlink()

import database  # noqa: E402

database.DATABASE = str(DATABASE_PATH)

from app import app  # noqa: E402


def seed_test_users():
    """Create accounts used only by Playwright against the disposable database."""
    users = [
        ("E2E HR", "e2e-hr@example.test", "E2eHrPassword!", "hr"),
        ("E2E Admin", "e2e-admin@example.test", "E2eAdminPassword!", "admin"),
        ("E2E Candidate", "e2e-candidate@example.test", "E2eCandidatePassword!", "candidate"),
    ]
    for name, email, password, role in users:
        user_id = database.register_user(
            name,
            os.environ.get(f"E2E_{role.upper()}_EMAIL", email),
            os.environ.get(f"E2E_{role.upper()}_PASSWORD", password),
            role,
            force_password_change=0,
        )
        if role == "candidate":
            # Gives the HR Talent Search test a real candidate profile while
            # remaining independent from the candidate onboarding test.
            database.save_candidate_profile(user_id, {
                "phone": "+91 9000000000",
                "location": "Hyderabad",
                "current_company": "E2E Systems",
                "designation": "Python Developer",
                "experience_years": 2,
                "notice_period": "30 days",
                "expected_salary": "",
                "linkedin_url": "",
                "portfolio_url": "",
                "skills": "Python, Flask, SQL",
                "education": "B.Tech",
                "photo_path": None,
                "resume_path": None,
                "resume_original_name": None,
                "profile_completed": False,
            })


if __name__ == "__main__":
    seed_test_users()
    app.run(host="127.0.0.1", port=5000, debug=False)

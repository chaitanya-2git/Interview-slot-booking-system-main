"""End-to-end smoke checks using an isolated temporary SQLite database.

Run with the project Python environment:
    python smoke_test.py
"""
import os
import tempfile

import database
from app import app


def expect(response, status, label):
    assert response.status_code == status, (
        f"{label}: expected {status}, got {response.status_code}"
    )


def main():
    fd, test_db = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(test_db)
    database.DATABASE = test_db

    try:
        database.create_tables()
        database.initialize_default_licenses_and_slots()
        database.create_default_hr_account()
        app.config.update(TESTING=True, SECRET_KEY="smoke-test-secret")

        hr = app.test_client()
        candidate = app.test_client()

        # Public pages and authentication / forced password change.
        expect(hr.get("/"), 302, "home redirect")
        response = hr.post(
            "/login", data={"email": "hr@blujay.com", "password": "password123"}
        )
        expect(response, 302, "HR login")
        assert response.headers["Location"].endswith("/change-password")
        expect(hr.get("/hr-dashboard"), 302, "forced password change guard")
        response = hr.post(
            "/change-password",
            data={"new_password": "HrPassword123!", "confirm_password": "HrPassword123!"},
        )
        expect(response, 302, "HR password change")
        expect(hr.get("/hr-dashboard"), 200, "HR dashboard")

        # HR creates a candidate; the candidate completes first-login password change.
        response = hr.post(
            "/create-candidate",
            data={"name": "Smoke Candidate", "email": "smoke@example.com", "password": "Candidate123!"},
        )
        expect(response, 302, "candidate creation")
        response = candidate.post(
            "/login", data={"email": "smoke@example.com", "password": "Candidate123!"}
        )
        expect(response, 302, "candidate login")
        assert response.headers["Location"].endswith("/change-password")
        response = candidate.post(
            "/change-password",
            data={"new_password": "Candidate456!", "confirm_password": "Candidate456!"},
        )
        expect(response, 302, "candidate password change")
        expect(candidate.get("/candidate-dashboard"), 200, "candidate dashboard")

        # Candidate obtains generated slots, books one, changes it, and cancels it.
        interview_date = "2030-01-15"
        response = candidate.get(f"/available-slots-by-date?interview_date={interview_date}")
        expect(response, 200, "available slots")
        blocks = response.get_json()["time_blocks"]
        assert blocks and blocks[0]["available"] > 0, "generated slots are available"
        first_time = blocks[0]["start_time"]
        response = candidate.post(
            "/book-slot",
            data={
                "interview_date": interview_date,
                "start_time": first_time,
                "company_name": "Example Corp",
                "technology": "Python",
                "interview_round": "Technical",
                "remarks": "Smoke test",
            },
        )
        expect(response, 302, "candidate booking")

        candidate_user = next(u for u in database.get_candidates() if u["email"] == "smoke@example.com")
        booking = database.get_user_bookings(candidate_user["id"])[0]
        alternate_time = next(b["start_time"] for b in blocks if b["start_time"] != first_time)
        response = candidate.post(
            f"/candidate-change-slot/{booking['id']}",
            data={"interview_date": interview_date, "new_slot_id": alternate_time},
        )
        expect(response, 302, "candidate reschedule")
        rescheduled_booking = database.get_booking_by_id(booking["id"])
        assert rescheduled_booking["start_time"] == alternate_time, "slot was rescheduled"
        response = candidate.post(f"/candidate-cancel-booking/{booking['id']}")
        expect(response, 302, "candidate cancellation")

        # The protected AJAX endpoint rejects unauthenticated access.
        anonymous = app.test_client()
        expect(anonymous.get("/available-slots-by-date?interview_date=2030-01-15"), 401, "authorization")

        print("Smoke tests passed: authentication, candidate management, slot booking, rescheduling, cancellation, and access controls.")
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)


if __name__ == "__main__":
    main()

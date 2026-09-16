import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from resume_parser import parse_resume
from database import register_user, login_user, get_user_by_id, get_all_users
from database import create_interview_slot, get_all_interview_slots, get_interview_slot_by_id, update_interview_slot, delete_interview_slot
from database import get_available_slots, create_booking, get_user_bookings, get_all_bookings, get_todays_interviews, reschedule_interview
from database import create_license, get_all_licenses, get_license_by_id
from database import get_booking_by_id, update_booking, cancel_booking
from database import create_notification, get_notifications, mark_notification_read, get_unread_notification_count
from database import get_dashboard_stats, get_candidate_dashboard_stats, get_candidate_interview_history, complete_interview
from database import assign_support_person, create_previous_interview_history, get_previous_interview_history
from database import get_slots_by_date, generate_slots_for_date, generate_slots_for_date_safe
from database import (
    get_user_by_id,
    get_all_licenses,
    create_interview_slot,
    create_booking,
    change_user_password,
    get_candidates,
    update_candidate,
    update_user_status,
    reset_user_password
)
from database import get_candidate_profile, save_candidate_profile, search_candidates, clear_candidate_resume

app_routes = Blueprint('main', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'resumes')
PHOTO_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads', 'photos')
ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
ALLOWED_PHOTO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_PHOTO_SIZE = 2 * 1024 * 1024


def allowed_resume(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS


def allowed_photo(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS


# India is UTC+05:30 year-round and does not observe daylight saving time.
APP_TIMEZONE = timezone(timedelta(hours=5, minutes=30))


def slot_has_started(interview_date, start_time, now=None):
    """Return True when a slot is earlier than the current India time."""
    try:
        slot_date = datetime.strptime(interview_date, '%Y-%m-%d').date()
        slot_clock = next(
            datetime.strptime(str(start_time).strip().upper(), pattern).time()
            for pattern in ('%I:%M %p', '%H:%M', '%H:%M:%S')
        )
    except (TypeError, ValueError, StopIteration):
        return False

    current = now or datetime.now(APP_TIMEZONE)
    if slot_date < current.date():
        return True
    if slot_date > current.date():
        return False
    return slot_clock < current.timetz().replace(tzinfo=None)


def password_change_required():
    """Keep first-login accounts on the password-change screen until complete."""
    if 'user_id' not in session:
        return False
    user = get_user_by_id(session['user_id'])
    return bool(user and user.get('force_password_change'))


@app_routes.before_request
def enforce_password_change():
    """Prevent forced-change accounts from bypassing the password page by URL."""
    if session.get('user_id'):
        current_user = get_user_by_id(session['user_id'])
        if not current_user or not current_user['is_active']:
            session.clear()
            return redirect(url_for('main.login'))
    if session.get('user_id'):
        session['user_role'] = current_user['role']
    allowed_endpoints = {
        'main.home', 'main.login', 'main.logout', 'main.register',
        'main.change_password'
    }
    if request.endpoint not in allowed_endpoints and password_change_required():
        return redirect(url_for('main.change_password'))

@app_routes.route('/', methods=['GET'])
def home():
    return redirect(url_for('main.login'))

@app_routes.route('/register', methods=['GET', 'POST'])
def register():
    # Public registration is disabled - candidates must be created by HR
    flash('Public registration is disabled. Please contact HR for account creation.', 'error')
    return redirect(url_for('main.home'))

@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = login_user(email, password)
        
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            
            # Check if user needs to change password
            force_password_change = user['force_password_change'] if 'force_password_change' in user else 0
            if force_password_change == 1:
                flash('You must change your password before continuing.', 'info')
                return redirect(url_for('main.change_password'))
            
            if user['role'] in ('hr', 'admin'):
                return redirect(url_for('main.hr_dashboard'))
            else:
                return redirect(url_for('main.candidate_dashboard'))
        else:
            flash('Invalid email or password or account is inactive.', 'error')
    
    return render_template('login.html')

@app_routes.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))

@app_routes.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash('Please fill in all fields.', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('change_password.html')
        
        # Change password
        change_user_password(session['user_id'], new_password)
        flash('Password changed successfully!', 'success')
        
        # Redirect to appropriate dashboard
        if session['user_role'] in ('hr', 'admin'):
            return redirect(url_for('main.hr_dashboard'))
        else:
            return redirect(url_for('main.candidate_dashboard'))
    
    return render_template('change_password.html')

@app_routes.route('/hr-dashboard')
def hr_dashboard():
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    if password_change_required():
        return redirect(url_for('main.change_password'))
    slots = get_all_interview_slots()
    bookings = get_all_bookings()
    todays_bookings = get_todays_interviews()
    from database import build_today_schedule
    today_schedule, other_today_bookings = build_today_schedule(todays_bookings)
    licenses = get_all_licenses()
    stats = get_dashboard_stats()
    notifications = get_notifications(session['user_id'], limit=10)
    unread_count = get_unread_notification_count(session['user_id'])
    return render_template('hr_dashboard.html', user_name=session['user_name'], slots=slots, bookings=bookings, todays_bookings=todays_bookings, today_schedule=today_schedule, other_today_bookings=other_today_bookings, licenses=licenses, stats=stats, notifications=notifications, unread_count=unread_count)

@app_routes.route('/todays-interviews')
def todays_interviews():
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    todays_bookings = get_todays_interviews()
    from database import build_today_schedule
    today_schedule, other_today_bookings = build_today_schedule(todays_bookings)
    licenses = get_all_licenses()
    stats = get_dashboard_stats()
    notifications = get_notifications(session['user_id'], limit=10)
    unread_count = get_unread_notification_count(session['user_id'])
    return render_template('hr_dashboard.html', user_name=session['user_name'], todays_bookings=todays_bookings, today_schedule=today_schedule, other_today_bookings=other_today_bookings, licenses=licenses, stats=stats, notifications=notifications, unread_count=unread_count)

@app_routes.route('/candidate-dashboard')
def candidate_dashboard():
    if 'user_id' not in session or session['user_role'] != 'candidate':
        return redirect(url_for('main.home'))
    if password_change_required():
        return redirect(url_for('main.change_password'))

    available_slots = []

    license1_slots = [
        slot for slot in available_slots
        if slot["license_name"] == "Earth"
    ]

    license2_slots = [
        slot for slot in available_slots
        if slot["license_name"] == "Moon"
    ]

    user_bookings = get_user_bookings(session['user_id'])
    licenses = get_all_licenses()
    stats = get_candidate_dashboard_stats(session['user_id'])
    notifications = get_notifications(session['user_id'], limit=10)
    unread_count = get_unread_notification_count(session['user_id'])
    previous_history = get_previous_interview_history(session['user_id'])
    profile = get_candidate_profile(session['user_id'])

    return render_template(
        'candidate_dashboard.html',
        user_name=session['user_name'],
        available_slots=available_slots,
        license1_slots=license1_slots,
        license2_slots=license2_slots,
        user_bookings=user_bookings,
        licenses=licenses,
        stats=stats,
        notifications=notifications,
        unread_count=unread_count,
        previous_history=previous_history,
        profile=profile
    )
@app_routes.route('/available-slots-by-date', methods=['GET'])
def available_slots_by_date():
    """Get available slots for a specific date via AJAX."""
    if 'user_id' not in session or session['user_role'] != 'candidate':
        return jsonify({'error': 'Unauthorized'}), 401
    
    interview_date = request.args.get('interview_date')
    
    if not interview_date:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        # Ensure slots are generated if they don't exist
        generate_slots_for_date_safe(interview_date)
        
        # Now fetch ALL slots (both booked and available) for aggregation
        from database import get_all_slots_by_date
        all_slots = get_all_slots_by_date(interview_date)
        
        if all_slots is None:
            return jsonify({'error': 'Failed to get slots'}), 500
        
        # Filter out deprecated 09:00 AM slots
        valid_slots = [
            slot for slot in all_slots
            if slot['start_time'] != '09:00 AM'
            and not slot_has_started(interview_date, slot['start_time'])
        ]
        
        # Aggregate by start_time
        aggregated_blocks = {}
        for slot in valid_slots:
            time_key = slot['start_time']
            if time_key not in aggregated_blocks:
                aggregated_blocks[time_key] = {
                    'start_time': slot['start_time'],
                    'end_time': slot['end_time'],
                    'interview_date': slot['interview_date'],
                    'total': 0,
                    'available': 0
                }
            aggregated_blocks[time_key]['total'] += 1
            if slot['status'] == 'available':
                aggregated_blocks[time_key]['available'] += 1
                
        # Convert to list and sort by start time logically
        # The string format '10:00 AM' sorts alphabetically fine except for PM vs AM, 
        # but since we already generate them in order, we can rely on standard sorting if we convert to 24h, 
        # or we can just sort by the original list of timings. 
        # For simplicity, we can just return the values, JS can render them in order they appear
        blocks = list(aggregated_blocks.values())
        
        return jsonify({
            'success': True,
            'time_blocks': blocks
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app_routes.route('/book-slot', methods=['POST'])
def book_slot():
    if 'user_id' not in session or session['user_role'] != 'candidate':
        return redirect(url_for('main.home'))

    company_name = request.form.get('company_name')
    technology = request.form.get('technology')
    interview_round = request.form.get('interview_round')
    remarks = request.form.get('remarks')
    hr_name = request.form.get('hr_name')
    hr_number = request.form.get('hr_number')
    
    interview_date = request.form.get('interview_date')
    start_time = request.form.get('start_time')
    
    if not interview_date or not start_time:
        flash('Invalid request parameters.', 'error')
        return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

    if slot_has_started(interview_date, start_time):
        flash('That interview slot has already started or passed. Please select a later time.', 'error')
        return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

    from database import create_booking_by_time
    booking_id = create_booking_by_time(
        session['user_id'],
        interview_date,
        start_time,
        company_name,
        technology,
        interview_round,
        remarks,
        hr_name,
        hr_number
    )

    if booking_id == 'max_bookings_reached':
        flash('Maximum booking limit reached. Please contact the administrator.', 'error')
        # Create notification for HR users
        hr_users = [u for u in get_all_users() if u['role'] in ('hr', 'admin')]
        for hr in hr_users:
            create_notification(hr['id'], 'booking_failed', f'Candidate attempted to book but reached max limit.')
    elif booking_id == 'fully_booked':
        flash('This interview slot has just been booked by another candidate. Please select another available slot.', 'error')
    elif booking_id:
        flash('Interview slot booked successfully!', 'success')
        # Create notification for candidate
        create_notification(session['user_id'], 'booking_success', 'Your interview slot has been booked successfully!')
        # Create notification for HR users
        hr_users = [u for u in get_all_users() if u['role'] in ('hr', 'admin')]
        for hr in hr_users:
            create_notification(hr['id'], 'new_booking', f'New candidate booked an interview slot.')
    elif booking_id == 'max_bookings_reached':
        flash('Maximum booking limit reached. Please contact the administrator.', 'error')
        # Create notification for HR users
        hr_users = [u for u in get_all_users() if u['role'] in ('hr', 'admin')]
        for hr in hr_users:
            create_notification(hr['id'], 'max_bookings', f'A candidate reached maximum booking limit.')
    else:
        flash('Failed to book slot. It may already be booked.', 'error')

    return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

@app_routes.route('/create-slot', methods=['GET', 'POST'])
def create_slot():
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    licenses = get_all_licenses()
    
    if request.method == 'POST':
        license_id = request.form['license_id']
        interview_date = request.form['interview_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        status = request.form.get('status', 'available')
        
        create_interview_slot(int(license_id), interview_date, start_time, end_time, status)
        flash('Interview slot created successfully!', 'success')
        return redirect(url_for('main.hr_dashboard', _anchor='available-slots'))
    
    return render_template('create_slot.html', licenses=licenses)

@app_routes.route('/edit-slot/<int:slot_id>', methods=['GET', 'POST'])
def edit_slot(slot_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    slot = get_interview_slot_by_id(slot_id)
    licenses = get_all_licenses()
    
    if not slot:
        flash('Booking not found!', 'error')
        return redirect(url_for('main.hr_dashboard', _anchor='bookings'))
    
    if request.method == 'POST':
        license_id = request.form['license_id']
        interview_date = request.form['interview_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        status = request.form.get('status', 'available')
        
        update_interview_slot(slot_id, int(license_id), interview_date, start_time, end_time, status)
        flash('Interview slot updated successfully!', 'success')
        return redirect(url_for('main.hr_dashboard', _anchor='available-slots'))
    
    return render_template('edit_slot.html', slot=slot, licenses=licenses)

@app_routes.route('/delete-slot/<int:slot_id>', methods=['POST'])
def delete_slot(slot_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    delete_interview_slot(slot_id)
    flash('Interview slot deleted successfully!', 'success')
    return redirect(url_for('main.hr_dashboard', _anchor='available-slots'))

@app_routes.route("/reschedule/<int:booking_id>", methods=['GET', 'POST'])
def reschedule_interview_route(booking_id):
    # Check for AJAX request using X-Requested-With header
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    print(f"DEBUG: /reschedule/{booking_id} - Method: {request.method}, is_ajax: {is_ajax}, X-Requested-With: {request.headers.get('X-Requested-With')}")

    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        print(f"DEBUG: Unauthorized - user_id in session: {'user_id' in session}, user_role: {session.get('user_role')}")
        if is_ajax:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return redirect(url_for('main.home'))

    booking = get_booking_by_id(booking_id)
    print(f"DEBUG: Booking found: {booking is not None}")

    if not booking:
        if is_ajax:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
        flash("Booking not found", "error")
        return redirect(url_for('main.hr_dashboard', _anchor='bookings'))

    # Get available slots for the same interview date
    available_slots = get_available_slots(booking["interview_date"])
    print(f"DEBUG: Available slots count: {len(available_slots) if available_slots else 0}")

    if request.method == 'POST':
        start_time = request.form.get('new_slot_id') # Form submits start_time in the new_slot_id field
        interview_date = request.form.get('interview_date')

        if start_time and interview_date:
            from database import reschedule_interview_by_time
            result = reschedule_interview_by_time(booking_id, interview_date, start_time)

            if result:
                if is_ajax:
                    return jsonify({'success': True, 'message': 'Interview rescheduled successfully!'})
                flash('Interview rescheduled successfully!', 'success')
                create_notification(
                    booking['user_id'],
                    'interview_rescheduled',
                    'Your interview has been rescheduled by HR.'
                )
                return redirect(url_for('main.hr_dashboard', _anchor='bookings'))
            else:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'Failed to reschedule. The slot may no longer be available.'})
                flash('Failed to reschedule. The slot may no longer be available.', 'error')
                return redirect(url_for('main.hr_dashboard', _anchor='bookings'))

    # AJAX GET request - return partial HTML for modal
    if is_ajax:
        print(f"DEBUG: Returning partial HTML for modal")
        return render_template(
            "reschedule_interview_partial.html",
            booking=booking,
            available_slots=available_slots
        )

    # Regular GET request - return full page
    print(f"DEBUG: Returning full page")
    return render_template(
        "reschedule_interview.html",
        booking=booking,
        available_slots=available_slots
    )

@app_routes.route("/candidate-change-slot/<int:booking_id>", methods=['GET', 'POST'])
def candidate_change_slot(booking_id):
    # Check for AJAX request using X-Requested-With header
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if 'user_id' not in session or session['user_role'] != 'candidate':
        if is_ajax:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        return redirect(url_for('main.home'))

    booking = get_booking_by_id(booking_id)

    if not booking:
        if is_ajax:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
        flash("Booking not found", "error")
        return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

    # Verify booking belongs to the logged-in candidate
    if booking['user_id'] != session['user_id']:
        if is_ajax:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        flash("You can only change your own bookings", "error")
        return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

    # Handle AJAX request to load slots for a specific date
    if is_ajax and request.method == 'GET' and request.args.get('load_slots'):
        interview_date = request.args.get('interview_date')
        if not interview_date:
            return jsonify({'success': False, 'error': 'Date is required'}), 400

        # Generate slots if they don't exist (safe version)
        generate_slots_for_date_safe(interview_date)
        
        # Fetch all slots for aggregation
        from database import get_all_slots_by_date
        all_slots = get_all_slots_by_date(interview_date)
        
        if all_slots is None:
            return jsonify({'success': False, 'error': 'Failed to get slots'}), 500
            
        valid_slots = [
            slot for slot in all_slots
            if slot['start_time'] != '09:00 AM'
            and not slot_has_started(interview_date, slot['start_time'])
        ]
        
        # Aggregate by start_time
        aggregated_blocks = {}
        for slot in valid_slots:
            time_key = slot['start_time']
            if time_key not in aggregated_blocks:
                aggregated_blocks[time_key] = {
                    'start_time': slot['start_time'],
                    'end_time': slot['end_time'],
                    'interview_date': slot['interview_date'],
                    'total': 0,
                    'available': 0
                }
            aggregated_blocks[time_key]['total'] += 1
            if slot['status'] == 'available':
                aggregated_blocks[time_key]['available'] += 1
                
        blocks = list(aggregated_blocks.values())

        return jsonify({
            'success': True,
            'time_blocks': blocks
        })

    # Don't pre-load slots on initial GET - let user select a date first
    available_slots = []

    if request.method == 'POST':
        start_time = request.form.get('new_slot_id') # Form submits start_time in the new_slot_id field
        interview_date = request.form.get('interview_date')

        if start_time and interview_date:
            from database import reschedule_interview_by_time
            result = reschedule_interview_by_time(booking_id, interview_date, start_time)

            if result:
                if is_ajax:
                    return jsonify({'success': True, 'message': 'Slot changed successfully!'})
                flash('Slot changed successfully!', 'success')
                # Create notification for HR users
                hr_users = [u for u in get_all_users() if u['role'] in ('hr', 'admin')]
                for hr in hr_users:
                    create_notification(hr['id'], 'slot_changed', f'A candidate changed their interview slot.')
                return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))
            else:
                if is_ajax:
                    return jsonify({'success': False, 'error': 'Failed to change slot. The slot may no longer be available.'})
                flash('Invalid slot ID', 'error')
                return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

    # AJAX GET request - return partial HTML for modal
    if is_ajax:
        return render_template(
            "change_slot_partial.html",
            booking=booking,
            available_slots=available_slots
        )

    # Regular GET request - redirect to dashboard (change_slot.html doesn't exist)
    return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

    
@app_routes.route('/edit-booking/<int:booking_id>', methods=['GET', 'POST'])
def edit_booking(booking_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    booking = get_booking_by_id(booking_id)
    
    if not booking:
        flash('Booking not found!', 'error')
        return redirect(url_for('main.hr_dashboard', _anchor='bookings'))
    
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        technology = request.form.get('technology')
        interview_round = request.form.get('interview_round')
        remarks = request.form.get('remarks')
        
        update_booking(booking_id, company_name, technology, interview_round, remarks)
        flash('Booking updated successfully!', 'success')
        return redirect(url_for('main.hr_dashboard', _anchor='bookings'))
    
    return render_template('edit_booking.html', booking=booking)

@app_routes.route('/create-candidate-slot/<int:user_id>', methods=['GET', 'POST'])
def create_candidate_slot(user_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))

    candidate = get_user_by_id(user_id)

    if request.method == 'POST':
        license_id = request.form['license_id']
        interview_date = request.form['interview_date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        company_name = request.form['company_name']
        technology = request.form['technology']
        interview_round = request.form['interview_round']
        remarks = request.form['remarks']

        # Create a brand new slot
        slot_id = create_interview_slot(
            license_id,
            interview_date,
            start_time,
            end_time,
            'available'
        )

        # Book it directly for this candidate (override max bookings limit for HR-created slots)
        booking_id = create_booking(
            user_id,
            slot_id,
            company_name,
            technology,
            interview_round,
            remarks,
            override_max_bookings=True,
            interview_date=interview_date
        )

        if booking_id:
            flash("Extra interview slot created and booked successfully.", "success")
        else:
            flash("Slot created but booking failed. The slot may have been booked by another user.", "error")

        return redirect(url_for('main.hr_dashboard', _anchor='bookings'))

    licenses = get_all_licenses()

    return render_template(
        'create_candidate_slot.html',
        candidate=candidate,
        licenses=licenses
    )

@app_routes.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking_route(booking_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    booking = get_booking_by_id(booking_id)
    result = cancel_booking(booking_id)
    
    if result:
        flash('Booking cancelled successfully!', 'success')
        # Create notification for candidate
        if booking:
            create_notification(booking['user_id'], 'interview_cancelled', 'Your interview has been cancelled by HR.')
    else:
        flash('Failed to cancel booking.', 'error')
    
    return redirect(url_for('main.hr_dashboard', _anchor='bookings'))

@app_routes.route('/candidate-cancel-booking/<int:booking_id>', methods=['POST'])
def candidate_cancel_booking_route(booking_id):
    if 'user_id' not in session or session['user_role'] != 'candidate':
        return redirect(url_for('main.home'))
    
    booking = get_booking_by_id(booking_id)
    
    if not booking:
        flash('Booking not found.', 'error')
        return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))
    
    # Verify booking belongs to the logged-in candidate
    if booking['user_id'] != session['user_id']:
        flash('You can only cancel your own bookings.', 'error')
        return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))
    
    result = cancel_booking(booking_id)
    
    if result:
        flash('Booking cancelled successfully!', 'success')
        # Create notification for HR users
        hr_users = [u for u in get_all_users() if u['role'] in ('hr', 'admin')]
        for hr in hr_users:
            create_notification(hr['id'], 'booking_cancelled', f'A candidate cancelled their interview booking.')
    else:
        flash('Failed to cancel booking.', 'error')
    
    return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

@app_routes.route('/mark-notification-read/<int:notification_id>', methods=['POST'])
def mark_notification_read_route(notification_id):
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    
    mark_notification_read(notification_id)
    
    if session['user_role'] in ('hr', 'admin'):
        return redirect(url_for('main.hr_dashboard'))
    else:
        return redirect(url_for('main.candidate_dashboard'))

@app_routes.route('/candidate-history/<int:user_id>')
def candidate_history(user_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    candidate = get_user_by_id(user_id)
    history = get_candidate_interview_history(user_id)
    previous_history = get_previous_interview_history(user_id)
    
    return render_template('candidate_history.html', candidate=candidate, history=history, previous_history=previous_history)

@app_routes.route('/complete-interview/<int:booking_id>', methods=['GET', 'POST'])
def complete_interview_route(booking_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    booking = get_booking_by_id(booking_id)
    
    if request.method == 'POST':
        feedback = request.form.get('feedback')
        result = request.form.get('result')
        
        complete_interview(booking_id, feedback, result)
        
        # Create notification for candidate
        if booking:
            create_notification(booking['user_id'], 'interview_completed', 'Your interview has been completed. Result is now available.')
            create_notification(booking['user_id'], 'result_available', f'Interview result: {result}')
        
        flash('Interview marked as completed!', 'success')
        return redirect(url_for('main.hr_dashboard', _anchor='bookings'))
    
    return render_template('complete_interview.html', booking=booking)

@app_routes.route('/assign-support/<int:booking_id>', methods=['POST'])
def assign_support_person_route(booking_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    support_person = request.form.get('support_person')
    
    if support_person:
        assign_support_person(booking_id, support_person)
        flash('Support person assigned successfully!', 'success')
    else:
        flash('Please provide a support person name.', 'error')
    
    return redirect(url_for('main.hr_dashboard', _anchor='bookings'))

@app_routes.route('/add-previous-history', methods=['POST'])
def add_previous_history_route():
    if 'user_id' not in session or session['user_role'] != 'candidate':
        return redirect(url_for('main.home'))
    
    company_name = request.form.get('company_name')
    interview_round = request.form.get('interview_round')
    interview_date = request.form.get('interview_date')
    result = request.form.get('result')
    remarks = request.form.get('remarks')
    
    if company_name and interview_round and interview_date and result:
        create_previous_interview_history(
            session['user_id'],
            company_name,
            interview_round,
            interview_date,
            result,
            remarks
        )
        flash('Previous interview history added successfully!', 'success')
    else:
        flash('Please fill in all required fields.', 'error')
    
    return redirect(url_for('main.candidate_dashboard', _anchor='previous-status'))

@app_routes.route('/get-slots-by-date', methods=['POST'])
def get_slots_by_date_route():
    """Get or generate slots for a specific date via AJAX."""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    interview_date = request.json.get('interview_date')
    
    if not interview_date:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        # Generate slots for the date securely
        generate_slots_for_date_safe(interview_date)
        
        # Now fetch ALL slots (both booked and available) for aggregation
        from database import get_all_slots_by_date
        all_slots = get_all_slots_by_date(interview_date)
        
        if all_slots is None:
            return jsonify({'error': 'Failed to get slots'}), 500
        
        # Filter out deprecated 09:00 AM slots
        valid_slots = [
            slot for slot in all_slots
            if slot['start_time'] != '09:00 AM'
            and not slot_has_started(interview_date, slot['start_time'])
        ]
        
        # Aggregate by start_time
        aggregated_blocks = {}
        for slot in valid_slots:
            time_key = slot['start_time']
            if time_key not in aggregated_blocks:
                aggregated_blocks[time_key] = {
                    'start_time': slot['start_time'],
                    'end_time': slot['end_time'],
                    'interview_date': slot['interview_date'],
                    'total': 0,
                    'available': 0
                }
            aggregated_blocks[time_key]['total'] += 1
            if slot['status'] == 'available':
                aggregated_blocks[time_key]['available'] += 1
                
        blocks = list(aggregated_blocks.values())
        
        return jsonify({
            'success': True,
            'time_blocks': blocks
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app_routes.route('/manage-candidates')
def manage_candidates():
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    candidates = get_candidates()
    return render_template('manage_candidates.html', candidates=candidates)


@app_routes.route('/candidate-profile', methods=['GET', 'POST'])
def candidate_profile():
    """Candidate-owned onboarding profile and resume upload."""
    if session.get('user_role') != 'candidate':
        return redirect(url_for('main.home'))

    profile = get_candidate_profile(session['user_id'])

    def profile_progress(data):
        fields = ('phone', 'location', 'current_company', 'designation', 'experience_years', 'skills', 'education', 'resume_path')
        completed = sum(1 for field in fields if data and data.get(field) not in (None, ''))
        return completed, len(fields), round((completed / len(fields)) * 100)
    if request.method == 'POST':
        uploaded = request.files.get('resume')
        photo_upload = request.files.get('photo')
        resume_path = None
        resume_name = None
        photo_path = None
        pending_resume = session.get('pending_candidate_resume') or {}
        if photo_upload and photo_upload.filename and not allowed_photo(photo_upload.filename):
            flash('Upload a JPG, PNG, or WEBP profile photo.', 'error')
            completed, total, percent = profile_progress(profile)
            return render_template('candidate_profile.html', profile=profile, profile_completed_fields=completed, profile_total_fields=total, profile_percent=percent)
        if uploaded and uploaded.filename:
            if not allowed_resume(uploaded.filename):
                flash('Upload a PDF, DOC, or DOCX resume.', 'error')
                completed, total, percent = profile_progress(profile)
                return render_template('candidate_profile.html', profile=profile, profile_completed_fields=completed, profile_total_fields=total, profile_percent=percent)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            resume_name = secure_filename(uploaded.filename)
            stored_name = f"{session['user_id']}-{uuid4().hex}-{resume_name}"
            uploaded.save(os.path.join(UPLOAD_FOLDER, stored_name))
            resume_path = stored_name
            try:
                parsed = parse_resume(os.path.join(UPLOAD_FOLDER, stored_name))
            except Exception:
                parsed = {}
        else:
            parsed = {}
            # A resume parsed by the review step is saved only after the
            # candidate confirms the populated form.
            resume_path = pending_resume.get('path')
            resume_name = pending_resume.get('name')

        if photo_upload and photo_upload.filename:
            os.makedirs(PHOTO_UPLOAD_FOLDER, exist_ok=True)
            photo_name = secure_filename(photo_upload.filename)
            photo_path = f"{session['user_id']}-{uuid4().hex}-{photo_name}"
            saved_photo = os.path.join(PHOTO_UPLOAD_FOLDER, photo_path)
            photo_upload.save(saved_photo)
            if os.path.getsize(saved_photo) > MAX_PHOTO_SIZE:
                os.remove(saved_photo)
                flash('Profile photos must be 2 MB or smaller.', 'error')
                completed, total, percent = profile_progress(profile)
                return render_template('candidate_profile.html', profile=profile, profile_completed_fields=completed, profile_total_fields=total, profile_percent=percent)

        profile_data = {
            'phone': request.form.get('phone', '').strip() or parsed.get('phone', ''),
            'location': request.form.get('location', '').strip(),
            'current_company': request.form.get('current_company', '').strip(),
            'designation': request.form.get('designation', '').strip(),
            'experience_years': request.form.get('experience_years') or parsed.get('experience_years') or None,
            'notice_period': request.form.get('notice_period', '').strip(),
            'expected_salary': request.form.get('expected_salary', '').strip(),
            'linkedin_url': request.form.get('linkedin_url', '').strip(),
            'portfolio_url': profile.get('portfolio_url', ''),
            'skills': request.form.get('skills', '').strip() or parsed.get('skills', ''),
            'education': request.form.get('education', '').strip() or parsed.get('education', ''),
            'photo_path': photo_path,
            'resume_path': resume_path,
            'resume_original_name': resume_name,
        }
        effective_resume = resume_path or profile.get('resume_path')
        profile_data['profile_completed'] = bool(
            profile_data['phone'] and profile_data['location'] and profile_data['designation']
            and profile_data['experience_years'] and profile_data['skills'] and effective_resume
        )
        save_candidate_profile(session['user_id'], profile_data)
        if resume_path and profile.get('resume_path') and profile['resume_path'] != resume_path:
            previous_resume = os.path.join(UPLOAD_FOLDER, profile['resume_path'])
            if os.path.isfile(previous_resume):
                os.remove(previous_resume)
        if photo_path and profile.get('photo_path') and profile['photo_path'] != photo_path:
            previous_photo = os.path.join(PHOTO_UPLOAD_FOLDER, profile['photo_path'])
            if os.path.isfile(previous_photo):
                os.remove(previous_photo)
        # Notify recruiters only when this is the candidate's first completed
        # onboarding submission. Later edits should not create notification noise.
        if profile_data['profile_completed'] and not profile.get('profile_completed'):
            for recruiter in get_all_users():
                if recruiter.get('role') in ('hr', 'admin') and recruiter.get('is_active'):
                    create_notification(
                        recruiter['id'],
                        'candidate_onboarded',
                        f"New candidate onboarding completed: {profile['name']}."
                    )
        session.pop('pending_candidate_resume', None)
        flash('Profile saved successfully. Your candidate profile is ready for review.', 'success')
        return redirect(url_for('main.candidate_dashboard'))
    completed, total, percent = profile_progress(profile)
    return render_template('candidate_profile.html', profile=profile, profile_completed_fields=completed, profile_total_fields=total, profile_percent=percent)


@app_routes.route('/candidate-profile/parse-resume', methods=['POST'])
def parse_candidate_resume():
    """Upload a candidate resume temporarily and return safe parsed fields for review."""
    if session.get('user_role') != 'candidate':
        return jsonify({'success': False, 'message': 'Please sign in as a candidate.'}), 403

    uploaded = request.files.get('resume')
    if not uploaded or not uploaded.filename:
        return jsonify({'success': False, 'message': 'Choose a resume first.'}), 400
    if not allowed_resume(uploaded.filename):
        return jsonify({'success': False, 'message': 'Upload a PDF, DOC, or DOCX resume.'}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    resume_name = secure_filename(uploaded.filename)
    stored_name = f"{session['user_id']}-{uuid4().hex}-{resume_name}"
    stored_path = os.path.join(UPLOAD_FOLDER, stored_name)
    uploaded.save(stored_path)

    # Replacing an unconfirmed upload should not leave private files behind.
    previous_pending = session.get('pending_candidate_resume') or {}
    previous_pending_path = previous_pending.get('path')
    if previous_pending_path and previous_pending_path != stored_name:
        old_file = os.path.join(UPLOAD_FOLDER, previous_pending_path)
        if os.path.isfile(old_file):
            os.remove(old_file)

    try:
        parsed = parse_resume(stored_path)
    except Exception:
        parsed = {}
    session['pending_candidate_resume'] = {'path': stored_name, 'name': resume_name}
    return jsonify({
        'success': True,
        'resume_name': resume_name,
        'parsed': parsed,
        'message': 'Resume parsed. Review the extracted details before saving.'
    })


@app_routes.route('/candidate-resume/<int:user_id>')
def candidate_resume(user_id):
    """Authenticated resume download for its owner, HR, or Admin."""
    if 'user_id' not in session or (session['user_id'] != user_id and session['user_role'] not in ('hr', 'admin')):
        return redirect(url_for('main.home'))
    profile = get_candidate_profile(user_id)
    if not profile or not profile.get('resume_path'):
        flash('No resume is available for this candidate.', 'error')
        return redirect(request.referrer or url_for('main.home'))
    return send_from_directory(UPLOAD_FOLDER, profile['resume_path'], as_attachment=True,
                               download_name=profile.get('resume_original_name') or 'resume')


@app_routes.route('/candidate-photo/<int:user_id>')
def candidate_photo(user_id):
    """Serve a profile photo only to its owner, HR, or an administrator."""
    if 'user_id' not in session or (session['user_id'] != user_id and session.get('user_role') not in ('hr', 'admin')):
        return redirect(url_for('main.home'))
    profile = get_candidate_profile(user_id)
    if not profile or not profile.get('photo_path'):
        abort(404)
    return send_from_directory(PHOTO_UPLOAD_FOLDER, profile['photo_path'], conditional=True)


@app_routes.route('/candidate-resume/remove', methods=['POST'])
def remove_candidate_resume():
    if session.get('user_role') != 'candidate':
        return redirect(url_for('main.home'))
    profile = get_candidate_profile(session['user_id'])
    if profile and profile.get('resume_path'):
        resume_file = os.path.join(UPLOAD_FOLDER, profile['resume_path'])
        if os.path.isfile(resume_file):
            os.remove(resume_file)
        clear_candidate_resume(session['user_id'])
        flash('Resume removed. Upload a new resume to complete your profile.', 'success')
    return redirect(url_for('main.candidate_profile'))


@app_routes.route('/candidate-details/<int:user_id>')
def candidate_details(user_id):
    """Recruiter view of the candidate's onboarding profile and interviews."""
    if session.get('user_role') not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    candidate = get_candidate_profile(user_id)
    if not candidate:
        flash('Candidate was not found.', 'error')
        return redirect(url_for('main.manage_candidates'))
    bookings = get_user_bookings(user_id)
    return render_template('candidate_details.html', candidate=candidate, bookings=bookings)


@app_routes.route('/talent-search')
def talent_search():
    if session.get('user_role') not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    # Accept the older `skill` parameter too, so an already-open Talent Search
    # tab continues to work after the interface was simplified to one field.
    filters = {'query': (request.args.get('query', '') or request.args.get('skill', '')).strip()}
    try:
        candidates = search_candidates(query=filters['query'])
    except ValueError:
        candidates = []
        flash('Use a valid experience value such as "DevOps 5+ years".', 'error')
    return render_template('talent_search.html', candidates=candidates, filters=filters)

@app_routes.route('/create-candidate', methods=['GET', 'POST'])
def create_candidate():
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('create_candidate.html')
        
        user_id = register_user(name, email, password, 'candidate', is_active=1, force_password_change=0)
        
        if user_id:
            create_notification(
                user_id,
                'onboarding_reminder',
                'Welcome to BluJay Interviews. Complete your profile and upload your resume so recruiters can review your skills.'
            )
            flash('Candidate created successfully. They can sign in with the password you set.', 'success')
            return redirect(url_for('main.manage_candidates'))
        else:
            flash('Email already registered.', 'error')
            return render_template('create_candidate.html')
    
    return render_template('create_candidate.html')

@app_routes.route('/edit-candidate/<int:user_id>', methods=['GET', 'POST'])
def edit_candidate(user_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    candidate = get_user_by_id(user_id)
    
    if not candidate or candidate['role'] != 'candidate':
        flash('Candidate not found.', 'error')
        return redirect(url_for('main.manage_candidates'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if not name or not email:
            flash('Please fill in all fields.', 'error')
            return render_template('edit_candidate.html', candidate=candidate)
        
        success = update_candidate(user_id, name, email)
        
        if success:
            flash('Candidate updated successfully.', 'success')
            return redirect(url_for('main.manage_candidates'))
        else:
            flash('Email already registered.', 'error')
            return render_template('edit_candidate.html', candidate=candidate)
    
    return render_template('edit_candidate.html', candidate=candidate)

@app_routes.route('/toggle-candidate-status/<int:user_id>', methods=['POST'])
def toggle_candidate_status(user_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    candidate = get_user_by_id(user_id)
    
    if not candidate or candidate['role'] != 'candidate':
        flash('Candidate not found.', 'error')
        return redirect(url_for('main.manage_candidates'))
    
    # Toggle status
    is_active = candidate['is_active'] if 'is_active' in candidate else 1
    new_status = 0 if is_active == 1 else 1
    update_user_status(user_id, new_status)
    
    status_text = 'activated' if new_status == 1 else 'deactivated'
    flash(f'Candidate {status_text} successfully.', 'success')
    return redirect(url_for('main.manage_candidates'))

@app_routes.route('/reset-candidate-password/<int:user_id>', methods=['GET', 'POST'])
def reset_candidate_password(user_id):
    if 'user_id' not in session or session['user_role'] not in ('hr', 'admin'):
        return redirect(url_for('main.home'))
    
    candidate = get_user_by_id(user_id)
    
    if not candidate or candidate['role'] != 'candidate':
        flash('Candidate not found.', 'error')
        return redirect(url_for('main.manage_candidates'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        
        if not new_password:
            flash('Please provide a new password.', 'error')
            return render_template('reset_candidate_password.html', candidate=candidate)
        
        reset_user_password(user_id, new_password)
        flash('Password reset successfully. The candidate can sign in with the new password.', 'success')
        return redirect(url_for('main.manage_candidates'))
    
    return render_template('reset_candidate_password.html', candidate=candidate)

@app_routes.app_context_processor
def account_preferences():
    from database import get_db_connection
    preferences = {}
    if session.get('user_id'):
        conn = get_db_connection()
        try:
            row = conn.execute('SELECT larger_text, reduce_motion FROM user_preferences WHERE user_id = ?', (session['user_id'],)).fetchone()
            if row:
                preferences = dict(row)
        finally:
            conn.close()
    return {'account_preferences': preferences}


@app_routes.route('/settings', methods=['GET', 'POST'])
def settings():
    import re
    import secrets
    import sqlite3
    from werkzeug.security import check_password_hash
    from database import get_db_connection
    if not session.get('user_id'):
        return redirect(url_for('main.login'))
    user = get_user_by_id(session['user_id'])
    if not user or not user['is_active']:
        session.clear()
        return redirect(url_for('main.login'))
    session.setdefault('settings_csrf', secrets.token_urlsafe(32))
    error = None
    if request.method == 'POST':
        if not secrets.compare_digest(request.form.get('csrf_token', ''), session['settings_csrf']):
            return 'Please reload Settings and try again.', 400
        action = request.form.get('action')
        if action == 'profile':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip().lower()
            if not name or len(name) > 100:
                error = 'Enter a name between 1 and 100 characters.'
            elif len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                error = 'Enter a valid email address.'
            elif email != user['email'] and not check_password_hash(user['password'], request.form.get('current_password', '')):
                error = 'Enter your current password to change your email address.'
            else:
                conn = get_db_connection()
                try:
                    duplicate = conn.execute('SELECT id FROM users WHERE lower(email) = ? AND id != ?', (email, user['id'])).fetchone()
                    if duplicate:
                        error = 'That email address is already in use.'
                    else:
                        with conn:
                            conn.execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, user['id']))
                        session['user_name'] = name
                except sqlite3.IntegrityError:
                    error = 'That email address is already in use.'
                finally:
                    conn.close()
        elif action == 'password':
            password = request.form.get('new_password', '')
            if not check_password_hash(user['password'], request.form.get('current_password', '')):
                error = 'Your current password is incorrect.'
            elif len(password) < 8:
                error = 'Use at least 8 characters for your new password.'
            elif password != request.form.get('confirm_password'):
                error = 'The new passwords do not match.'
            elif check_password_hash(user['password'], password):
                error = 'Choose a password different from your current password.'
            else:
                change_user_password(user['id'], password)
        elif action == 'preferences':
            conn = get_db_connection()
            try:
                with conn:
                    conn.execute('INSERT INTO user_preferences (user_id, larger_text, reduce_motion) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET larger_text = excluded.larger_text, reduce_motion = excluded.reduce_motion', (user['id'], int(request.form.get('larger_text') == 'on'), int(request.form.get('reduce_motion') == 'on')))
            finally:
                conn.close()
        else:
            error = 'Choose a valid settings action.'
        if not error:
            flash('Settings saved successfully.', 'success')
            return redirect(url_for('main.settings'))
    return render_template('settings.html', user=user, settings_error=error)


@app_routes.route('/delete-candidate/<int:user_id>', methods=['GET', 'POST'])
def delete_candidate(user_id):
    import secrets
    from database import delete_candidate_account
    actor = get_user_by_id(session['user_id']) if session.get('user_id') else None
    if not actor or actor['role'] not in ('hr', 'admin') or not actor['is_active']:
        return 'Only HR or administrators can delete candidates.', 403
    candidate = get_user_by_id(user_id)
    if not candidate or candidate['role'] != 'candidate':
        return 'Candidate not found.', 404
    candidate_profile_data = get_candidate_profile(user_id)
    session.setdefault('delete_candidate_csrf', secrets.token_urlsafe(32))
    error = None
    if request.method == 'POST':
        if not secrets.compare_digest(request.form.get('csrf_token', ''), session['delete_candidate_csrf']):
            return 'Please reload the confirmation page and try again.', 400
        if request.form.get('confirmation') != candidate['email']:
            error = 'Enter the candidate email exactly to confirm deletion.'
        elif delete_candidate_account(user_id):
            # The database record has been removed; delete the private resume
            # file afterwards when it exists. A missing file is harmless.
            if candidate_profile_data and candidate_profile_data.get('resume_path'):
                resume_file = os.path.join(UPLOAD_FOLDER, candidate_profile_data['resume_path'])
                if os.path.isfile(resume_file):
                    os.remove(resume_file)
            if candidate_profile_data and candidate_profile_data.get('photo_path'):
                photo_file = os.path.join(PHOTO_UPLOAD_FOLDER, candidate_profile_data['photo_path'])
                if os.path.isfile(photo_file):
                    os.remove(photo_file)
            flash('Candidate and related records deleted successfully.', 'success')
            return redirect(url_for('main.manage_candidates'))
        else:
            return 'Candidate not found.', 404
    return render_template('delete_candidate.html', candidate=candidate, deletion_error=error)


@app_routes.route('/manage-admins', methods=['GET', 'POST'])
def manage_admins():
    import re
    import secrets
    from database import get_db_connection
    actor = get_user_by_id(session['user_id']) if session.get('user_id') else None
    if not actor or actor['role'] != 'admin' or not actor['is_active']:
        return 'Only administrators can manage admin accounts.', 403
    session.setdefault('admin_csrf', secrets.token_urlsafe(32))
    error = None
    if request.method == 'POST':
        if not secrets.compare_digest(request.form.get('csrf_token', ''), session['admin_csrf']):
            return 'Please reload Manage Admins and try again.', 400
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or len(name) > 100:
            error = 'Enter a name between 1 and 100 characters.'
        elif len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            error = 'Enter a valid email address.'
        elif len(password) < 8:
            error = 'Use at least 8 characters for the password.'
        elif password != request.form.get('confirm_password'):
            error = 'The passwords do not match.'
        else:
            conn = get_db_connection()
            try:
                duplicate = conn.execute('SELECT id FROM users WHERE lower(email) = ?', (email,)).fetchone()
            finally:
                conn.close()
            if duplicate:
                error = 'That email address is already in use.'
            elif register_user(name, email, password, 'admin', is_active=1, force_password_change=0):
                flash('Admin created. Share their login email and password.', 'success')
                return redirect(url_for('main.manage_admins'))
            else:
                error = 'That email address is already in use.'
    conn = get_db_connection()
    try:
        admins = conn.execute("SELECT id, name, email, is_active, force_password_change FROM users WHERE role = 'admin' ORDER BY id").fetchall()
    finally:
        conn.close()
    return render_template('manage_admins.html', admins=admins, admin_error=error)

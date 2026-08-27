from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
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

app_routes = Blueprint('main', __name__)

@app_routes.route('/', methods=['GET', 'POST'])
def home():
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
            
            if user['role'] == 'hr':
                return redirect(url_for('main.hr_dashboard'))
            else:
                return redirect(url_for('main.candidate_dashboard'))
        else:
            flash('Invalid email or password or account is inactive.', 'error')
    
    return render_template('index.html')

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
            
            if user['role'] == 'hr':
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
        if session['user_role'] == 'hr':
            return redirect(url_for('main.hr_dashboard'))
        else:
            return redirect(url_for('main.candidate_dashboard'))
    
    return render_template('change_password.html')

@app_routes.route('/hr-dashboard')
def hr_dashboard():
    if 'user_id' not in session or session['user_role'] != 'hr':
        return redirect(url_for('main.home'))
    slots = get_all_interview_slots()
    bookings = get_all_bookings()
    todays_bookings = get_todays_interviews()
    licenses = get_all_licenses()
    stats = get_dashboard_stats()
    notifications = get_notifications(session['user_id'], limit=10)
    unread_count = get_unread_notification_count(session['user_id'])
    return render_template('hr_dashboard.html', user_name=session['user_name'], slots=slots, bookings=bookings, todays_bookings=todays_bookings, licenses=licenses, stats=stats, notifications=notifications, unread_count=unread_count)

@app_routes.route('/todays-interviews')
def todays_interviews():
    if 'user_id' not in session or session['user_role'] != 'hr':
        return redirect(url_for('main.home'))
    todays_bookings = get_todays_interviews()
    licenses = get_all_licenses()
    stats = get_dashboard_stats()
    notifications = get_notifications(session['user_id'], limit=10)
    unread_count = get_unread_notification_count(session['user_id'])
    return render_template('hr_dashboard.html', user_name=session['user_name'], todays_bookings=todays_bookings, licenses=licenses, stats=stats, notifications=notifications, unread_count=unread_count)

@app_routes.route('/candidate-dashboard')
def candidate_dashboard():
    if 'user_id' not in session or session['user_role'] != 'candidate':
        return redirect(url_for('main.home'))

    available_slots = []

    print("Candidate available slots:", len(available_slots))
    print(available_slots[:3])

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
        previous_history=previous_history
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
        valid_slots = [slot for slot in all_slots if slot['start_time'] != '09:00 AM']
        
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
        hr_users = [u for u in get_all_users() if u['role'] == 'hr']
        for hr in hr_users:
            create_notification(hr['id'], 'booking_failed', f'Candidate attempted to book but reached max limit.')
    elif booking_id == 'fully_booked':
        flash('This interview slot has just been booked by another candidate. Please select another available slot.', 'error')
    elif booking_id:
        flash('Interview slot booked successfully!', 'success')
        # Create notification for candidate
        create_notification(session['user_id'], 'booking_success', 'Your interview slot has been booked successfully!')
        # Create notification for HR users
        hr_users = [u for u in get_all_users() if u['role'] == 'hr']
        for hr in hr_users:
            create_notification(hr['id'], 'new_booking', f'New candidate booked an interview slot.')
    elif booking_id == 'max_bookings_reached':
        flash('Maximum booking limit reached. Please contact the administrator.', 'error')
        # Create notification for HR users
        hr_users = [u for u in get_all_users() if u['role'] == 'hr']
        for hr in hr_users:
            create_notification(hr['id'], 'max_bookings', f'A candidate reached maximum booking limit.')
    else:
        flash('Failed to book slot. It may already be booked.', 'error')

    return redirect(url_for('main.candidate_dashboard', _anchor='my-bookings'))

@app_routes.route('/create-slot', methods=['GET', 'POST'])
def create_slot():
    if 'user_id' not in session or session['user_role'] != 'hr':
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
    if 'user_id' not in session or session['user_role'] != 'hr':
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
    if 'user_id' not in session or session['user_role'] != 'hr':
        return redirect(url_for('main.home'))
    
    delete_interview_slot(slot_id)
    flash('Interview slot deleted successfully!', 'success')
    return redirect(url_for('main.hr_dashboard', _anchor='available-slots'))

@app_routes.route("/reschedule/<int:booking_id>", methods=['GET', 'POST'])
def reschedule_interview_route(booking_id):
    # Check for AJAX request using X-Requested-With header
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    print(f"DEBUG: /reschedule/{booking_id} - Method: {request.method}, is_ajax: {is_ajax}, X-Requested-With: {request.headers.get('X-Requested-With')}")

    if 'user_id' not in session or session['user_role'] != 'hr':
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
            
        valid_slots = [slot for slot in all_slots if slot['start_time'] != '09:00 AM']
        
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
                hr_users = [u for u in get_all_users() if u['role'] == 'hr']
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
    if 'user_id' not in session or session['user_role'] != 'hr':
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
    if 'user_id' not in session or session['user_role'] != 'hr':
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
    if 'user_id' not in session or session['user_role'] != 'hr':
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
        hr_users = [u for u in get_all_users() if u['role'] == 'hr']
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
    
    if session['user_role'] == 'hr':
        return redirect(url_for('main.hr_dashboard'))
    else:
        return redirect(url_for('main.candidate_dashboard'))

@app_routes.route('/candidate-history/<int:user_id>')
def candidate_history(user_id):
    if 'user_id' not in session or session['user_role'] != 'hr':
        return redirect(url_for('main.home'))
    
    candidate = get_user_by_id(user_id)
    history = get_candidate_interview_history(user_id)
    previous_history = get_previous_interview_history(user_id)
    
    return render_template('candidate_history.html', candidate=candidate, history=history, previous_history=previous_history)

@app_routes.route('/complete-interview/<int:booking_id>', methods=['GET', 'POST'])
def complete_interview_route(booking_id):
    if 'user_id' not in session or session['user_role'] != 'hr':
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
    if 'user_id' not in session or session['user_role'] != 'hr':
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
        valid_slots = [slot for slot in all_slots if slot['start_time'] != '09:00 AM']
        
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
    if 'user_id' not in session or session['user_role'] != 'hr':
        return redirect(url_for('main.home'))
    
    candidates = get_candidates()
    return render_template('manage_candidates.html', candidates=candidates)

@app_routes.route('/create-candidate', methods=['GET', 'POST'])
def create_candidate():
    if 'user_id' not in session or session['user_role'] != 'hr':
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('create_candidate.html')
        
        # Create candidate with force_password_change=1
        user_id = register_user(name, email, password, 'candidate', is_active=1, force_password_change=1)
        
        if user_id:
            flash('Candidate created successfully. They will be required to change their password on first login.', 'success')
            return redirect(url_for('main.manage_candidates'))
        else:
            flash('Email already registered.', 'error')
            return render_template('create_candidate.html')
    
    return render_template('create_candidate.html')

@app_routes.route('/edit-candidate/<int:user_id>', methods=['GET', 'POST'])
def edit_candidate(user_id):
    if 'user_id' not in session or session['user_role'] != 'hr':
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
    if 'user_id' not in session or session['user_role'] != 'hr':
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
    if 'user_id' not in session or session['user_role'] != 'hr':
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
        flash('Password reset successfully. The candidate will be required to change it on next login.', 'success')
        return redirect(url_for('main.manage_candidates'))
    
    return render_template('reset_candidate_password.html', candidate=candidate)

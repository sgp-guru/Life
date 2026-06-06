import os
import uuid
import json
import base64
from functools import wraps
from datetime import datetime, date

import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (Flask, render_template, redirect, url_for,
                   request, flash, session, jsonify)

# Location dataset helper
from locations import INDIA_LOCATIONS

# ─── Firebase Initialisation ──────────────────────────────────────────────────
# Supports both production (env var) and local development (json file)
fb_creds_b64 = os.environ.get('FIREBASE_CREDENTIALS_B64')
if fb_creds_b64:
    # Production: credentials passed as base64-encoded environment variable
    creds_dict = json.loads(base64.b64decode(fb_creds_b64).decode('utf-8'))
    cred = credentials.Certificate(creds_dict)
else:
    # Local development: read from file
    CRED_PATH = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')
    cred = credentials.Certificate(CRED_PATH)

firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore collection references
users_col      = db.collection('users')
donors_col     = db.collection('donors')
requests_col   = db.collection('blood_requests')

# ─── Flask App ────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'lifelink_super_secret_key_67890')

# ─── Firestore Helpers ────────────────────────────────────────────────────────

def fs_get_user_by_email(email):
    """Return the first user document dict matching email, or None."""
    docs = users_col.where(filter=firestore.FieldFilter('email', '==', email)).limit(1).stream()
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None

def fs_get_user_by_id(uid):
    doc = users_col.document(str(uid)).get()
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None

def fs_get_user_by_username(username):
    docs = users_col.where(filter=firestore.FieldFilter('username', '==', username)).limit(1).stream()
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None

def fs_create_user(email, password, is_admin=False):
    username = email.split('@')[0]
    # Ensure username uniqueness
    base = username
    count = 1
    while fs_get_user_by_username(username):
        username = f"{base}{count}"
        count += 1
    uid = str(uuid.uuid4())
    users_col.document(uid).set({
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'is_admin': is_admin,
        'created_at': firestore.SERVER_TIMESTAMP,
    })
    return uid, username

def fs_get_donor_by_user(uid):
    docs = donors_col.where(filter=firestore.FieldFilter('user_id', '==', uid)).limit(1).stream()
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None

def fs_get_donor_by_id(did):
    doc = donors_col.document(did).get()
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None

def fs_query_donors(blood_group=None, state=None, city=None):
    query = donors_col
    if blood_group:
        query = query.where(filter=firestore.FieldFilter('blood_group', '==', blood_group))
    if state:
        query = query.where(filter=firestore.FieldFilter('state', '==', state))
    if city:
        query = query.where(filter=firestore.FieldFilter('city', '==', city))
    docs = query.stream()
    result = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        result.append(data)
    # Sort: available donors first
    result.sort(key=lambda x: x.get('is_available', False), reverse=True)
    return result

def fs_get_all_donors():
    result = []
    for doc in donors_col.stream():
        data = doc.to_dict()
        data['id'] = doc.id
        result.append(data)
    return result

def fs_get_all_users():
    result = []
    for doc in users_col.stream():
        data = doc.to_dict()
        data['id'] = doc.id
        result.append(data)
    return result

def fs_get_request_by_id(rid):
    doc = requests_col.document(rid).get()
    if doc.exists:
        data = doc.to_dict()
        data['id'] = doc.id
        return data
    return None

def fs_get_all_requests():
    result = []
    for doc in requests_col.order_by('created_at', direction=firestore.Query.DESCENDING).stream():
        data = doc.to_dict()
        data['id'] = doc.id
        result.append(data)
    return result

def fs_get_active_requests():
    result = []
    for doc in requests_col.where(filter=firestore.FieldFilter('is_fulfilled', '==', False)).stream():
        data = doc.to_dict()
        data['id'] = doc.id
        result.append(data)
    return result

def date_to_str(d):
    """Convert date object to ISO string for Firestore storage."""
    if d is None:
        return None
    if isinstance(d, str):
        return d
    return d.isoformat()

def str_to_date(s):
    """Convert ISO string from Firestore back to date object."""
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        return None

# ─── Seed Default Data ────────────────────────────────────────────────────────

def seed_default_data():
    """Seed initial admin, donors and requests if Firestore is empty."""
    # Check if admin exists
    if fs_get_user_by_email('admin@lifelink.org'):
        return  # Already seeded

    print("Seeding Firestore with default data...")

    # Admin user
    admin_id = str(uuid.uuid4())
    users_col.document(admin_id).set({
        'username': 'admin',
        'email': 'admin@lifelink.org',
        'password_hash': generate_password_hash('admin123'),
        'is_admin': True,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    # John Doe
    john_id = str(uuid.uuid4())
    users_col.document(john_id).set({
        'username': 'john_doe',
        'email': 'john@gmail.com',
        'password_hash': generate_password_hash('password123'),
        'is_admin': False,
        'created_at': firestore.SERVER_TIMESTAMP,
    })
    donors_col.document(str(uuid.uuid4())).set({
        'user_id': john_id,
        'name': 'John Doe',
        'age': 28,
        'gender': 'Male',
        'blood_group': 'O+',
        'phone': '+15551234567',
        'email': 'john@gmail.com',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'last_donation_date': '2026-03-15',
        'weight': 72.0,
        'is_available': True,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    # Jane Smith
    jane_id = str(uuid.uuid4())
    users_col.document(jane_id).set({
        'username': 'jane_smith',
        'email': 'jane@gmail.com',
        'password_hash': generate_password_hash('password123'),
        'is_admin': False,
        'created_at': firestore.SERVER_TIMESTAMP,
    })
    donors_col.document(str(uuid.uuid4())).set({
        'user_id': jane_id,
        'name': 'Jane Smith',
        'age': 32,
        'gender': 'Female',
        'blood_group': 'A-',
        'phone': '+15559876543',
        'email': 'jane@gmail.com',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'last_donation_date': '2026-01-10',
        'weight': 58.0,
        'is_available': True,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    # David Miller
    david_id = str(uuid.uuid4())
    users_col.document(david_id).set({
        'username': 'david_miller',
        'email': 'david@gmail.com',
        'password_hash': generate_password_hash('password123'),
        'is_admin': False,
        'created_at': firestore.SERVER_TIMESTAMP,
    })
    donors_col.document(str(uuid.uuid4())).set({
        'user_id': david_id,
        'name': 'David Miller',
        'age': 45,
        'gender': 'Male',
        'blood_group': 'B+',
        'phone': '+15552468135',
        'email': 'david@gmail.com',
        'city': 'Pune',
        'state': 'Maharashtra',
        'last_donation_date': None,
        'weight': 80.0,
        'is_available': False,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    # Emergency Requests
    requests_col.document(str(uuid.uuid4())).set({
        'patient_name': 'Robert Davis',
        'blood_group': 'B+',
        'hospital_name': 'City General Hospital',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'contact_name': 'Sarah Davis',
        'contact_phone': '+916543210987',
        'units_needed': 3,
        'required_by': '2026-06-25',
        'description': '',
        'is_fulfilled': False,
        'created_at': firestore.SERVER_TIMESTAMP,
    })
    requests_col.document(str(uuid.uuid4())).set({
        'patient_name': 'Emily Watson',
        'blood_group': 'O-',
        'hospital_name': 'St. Jude Medical Center',
        'city': 'Bengaluru',
        'state': 'Karnataka',
        'contact_name': 'James Watson',
        'contact_phone': '+915432109876',
        'units_needed': 2,
        'required_by': '2026-06-18',
        'description': '',
        'is_fulfilled': False,
        'created_at': firestore.SERVER_TIMESTAMP,
    })

    print("Firestore seeded successfully!")

seed_default_data()

# ─── Utility ──────────────────────────────────────────────────────────────────

def send_email_notification(to_email, subject, body):
    print("================ MOCK EMAIL NOTIFICATION ================")
    print(f"TO: {to_email}")
    print(f"SUBJECT: {subject}")
    print(f"BODY:\n{body}")
    print("=========================================================")

# ─── Auth Decorators ─────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_user_id' not in session:
            flash('Admin access required. Please log in.', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user_context():
    return dict(
        is_logged_in='user_id' in session,
        current_username=session.get('username') or session.get('admin_username', ''),
        is_admin='admin_user_id' in session,
        mock_mode=False
    )

# ─── API Endpoints ────────────────────────────────────────────────────────────

@app.route('/api/locations')
def get_locations():
    return jsonify(INDIA_LOCATIONS)

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    all_donors    = fs_get_all_donors()
    all_requests  = fs_get_all_requests()

    total_donors      = len(all_donors)
    available_donors  = sum(1 for d in all_donors if d.get('is_available'))
    completed_requests = sum(1 for r in all_requests if r.get('is_fulfilled'))

    recent_emergencies = [r for r in all_requests if not r.get('is_fulfilled')][:3]

    chart_data = {
        'O+': 32, 'A+': 24, 'B+': 30, 'AB+': 8,
        'O-': 3,  'A-': 2,  'B-': 1,  'AB-': 0
    }

    return render_template('home.html',
                           total_donors=total_donors,
                           available_donors=available_donors,
                           completed_requests=completed_requests,
                           recent_emergencies=recent_emergencies,
                           chart_data=chart_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name    = request.form.get('name')
        email   = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not name or not email or not message:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('contact'))

        print(f"CONTACT FEEDBACK: Name={name}, Email={email}, Subject={subject}, Msg={message}")
        flash('Thank you for contacting LifeLink! We have received your message.', 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html')

# ─── Authentication ───────────────────────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not email or not password:
            flash('Email and Password are required.', 'danger')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        if fs_get_user_by_email(email):
            flash('Email is already registered.', 'danger')
            return redirect(url_for('register'))

        uid, username = fs_create_user(email, password)
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return redirect(url_for('login'))

        user = fs_get_user_by_email(email)
        if user and check_password_hash(user.get('password_hash', ''), password):
            session['user_id']  = user['id']
            session['username'] = user.get('username', '')
            session['role']     = 'admin' if user.get('is_admin') else 'user'
            flash('Successfully logged in!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/password-reset', methods=['POST'])
def password_reset():
    email = request.form.get('email', '').strip()
    if not email:
        return jsonify({'success': False, 'message': 'Email address is required.'}), 400

    user = fs_get_user_by_email(email)
    if not user:
        return jsonify({'success': False, 'message': 'No account found with this email address.'}), 404

    send_email_notification(
        email,
        "LifeLink - Password Reset Request",
        f"Dear {user.get('username')},\n\nWe received a request to reset your password.\n"
        f"(Simulated link): http://localhost:5000/reset-password-action\n\nBest Regards,\nLifeLink Team"
    )
    return jsonify({'success': True, 'message': 'Simulated link printed in developer console!'})

# Authentication - Logout (regular users)
@app.route('/logout')
def logout():
    # Only clear user session, not admin session
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ─── Separate Admin Authentication ───────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_user_id' in session:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return redirect(url_for('admin_login'))

        user = fs_get_user_by_email(email)
        if user and user.get('is_admin') and check_password_hash(user.get('password_hash', ''), password):
            session['admin_user_id']  = user['id']
            session['admin_username'] = user.get('username', 'Admin')
            flash(f"Welcome back, {user.get('username')}! You are now in the Admin Control Panel.", 'success')
            return redirect(url_for('admin'))
        elif user and not user.get('is_admin'):
            flash('This account does not have administrator privileges.', 'danger')
        else:
            flash('Invalid admin credentials.', 'danger')
        return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_user_id', None)
    session.pop('admin_username', None)
    flash('You have been logged out of the Admin Panel.', 'info')
    return redirect(url_for('admin_login'))

# ─── Donor Routes ─────────────────────────────────────────────────────────────

@app.route('/find-donor')
def find_donor():
    blood_group = request.args.get('blood_group', '').strip()
    state       = request.args.get('state', '').strip()
    city        = request.args.get('city', '').strip()

    donors_list = fs_query_donors(
        blood_group=blood_group or None,
        state=state or None,
        city=city or None
    )

    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    return render_template('find_donor.html',
                           donors=donors_list,
                           blood_groups=blood_groups,
                           states_list=INDIA_LOCATIONS.keys(),
                           search_params={'blood_group': blood_group, 'state': state, 'city': city})

@app.route('/register-donor', methods=['GET', 'POST'])
@login_required
def register_donor():
    uid = session['user_id']

    if fs_get_donor_by_user(uid):
        flash('You are already registered as a donor! You can manage details on your dashboard.', 'info')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name              = request.form.get('name', '').strip()
        age               = request.form.get('age', '')
        gender            = request.form.get('gender', '')
        blood_group       = request.form.get('blood_group', '')
        phone             = request.form.get('phone', '').strip()
        email             = request.form.get('email', '').strip()
        state             = request.form.get('state', '')
        city              = request.form.get('city', '')
        last_donation_str = request.form.get('last_donation_date', '')
        weight            = request.form.get('weight', '')
        health_decl       = 'health_declaration' in request.form

        if not all([name, age, gender, blood_group, phone, email, state, city, weight]) or not health_decl:
            flash('Please fill out all required fields and accept the health declaration.', 'danger')
            return redirect(url_for('register_donor'))

        try:
            age_val = int(age)
            if age_val < 18 or age_val > 65:
                flash('Age must be between 18 and 65.', 'danger')
                return redirect(url_for('register_donor'))
        except ValueError:
            flash('Invalid age format.', 'danger')
            return redirect(url_for('register_donor'))

        try:
            weight_val = float(weight)
            if weight_val < 50.0:
                flash('Weight must be at least 50 kg to donate blood.', 'danger')
                return redirect(url_for('register_donor'))
        except ValueError:
            flash('Invalid weight format.', 'danger')
            return redirect(url_for('register_donor'))

        last_donation_date = None
        if last_donation_str:
            try:
                datetime.strptime(last_donation_str, '%Y-%m-%d')
                last_donation_date = last_donation_str
            except ValueError:
                pass

        donors_col.document(str(uuid.uuid4())).set({
            'user_id':            uid,
            'name':               name,
            'age':                age_val,
            'gender':             gender,
            'blood_group':        blood_group,
            'phone':              phone,
            'email':              email,
            'state':              state,
            'city':               city,
            'last_donation_date': last_donation_date,
            'weight':             weight_val,
            'is_available':       True,
            'created_at':         firestore.SERVER_TIMESTAMP,
        })
        flash('Successfully registered as a blood donor!', 'success')
        return redirect(url_for('dashboard'))

    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    return render_template('register_donor.html',
                           blood_groups=blood_groups,
                           states_list=INDIA_LOCATIONS.keys())

@app.route('/dashboard')
@login_required
def dashboard():
    uid          = session['user_id']
    donor_profile = fs_get_donor_by_user(uid)
    return render_template('dashboard.html', donor=donor_profile)

@app.route('/dashboard/toggle-availability', methods=['POST'])
@login_required
def toggle_availability():
    uid        = session['user_id']
    data       = request.get_json()
    new_status = data.get('is_available')

    if new_status is None:
        return jsonify({'success': False, 'message': 'Missing parameter: is_available'}), 400

    donor = fs_get_donor_by_user(uid)
    if donor:
        donors_col.document(donor['id']).update({'is_available': bool(new_status)})
        return jsonify({'success': True, 'is_available': bool(new_status), 'message': 'Status updated.'})
    return jsonify({'success': False, 'message': 'Donor profile not found.'}), 404

@app.route('/dashboard/edit-donor', methods=['GET', 'POST'])
@login_required
def edit_donor():
    uid   = session['user_id']
    donor = fs_get_donor_by_user(uid)

    if not donor:
        flash('Donor record not found.', 'warning')
        return redirect(url_for('register_donor'))

    if request.method == 'POST':
        name              = request.form.get('name', '').strip()
        age               = request.form.get('age', '')
        gender            = request.form.get('gender', '')
        blood_group       = request.form.get('blood_group', '')
        phone             = request.form.get('phone', '').strip()
        email             = request.form.get('email', '').strip()
        state             = request.form.get('state', '')
        city              = request.form.get('city', '')
        last_donation_str = request.form.get('last_donation_date', '')
        weight            = request.form.get('weight', '')

        if not all([name, age, gender, blood_group, phone, email, state, city, weight]):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('edit_donor'))

        try:
            age_val = int(age)
            if age_val < 18 or age_val > 65:
                flash('Age must be between 18 and 65.', 'danger')
                return redirect(url_for('edit_donor'))
        except ValueError:
            flash('Invalid age format.', 'danger')
            return redirect(url_for('edit_donor'))

        try:
            weight_val = float(weight)
            if weight_val < 50.0:
                flash('Weight must be at least 50 kg.', 'danger')
                return redirect(url_for('edit_donor'))
        except ValueError:
            flash('Invalid weight format.', 'danger')
            return redirect(url_for('edit_donor'))

        last_donation_date = None
        if last_donation_str:
            try:
                datetime.strptime(last_donation_str, '%Y-%m-%d')
                last_donation_date = last_donation_str
            except ValueError:
                pass

        donors_col.document(donor['id']).update({
            'name':               name,
            'age':                age_val,
            'gender':             gender,
            'blood_group':        blood_group,
            'phone':              phone,
            'email':              email,
            'state':              state,
            'city':               city,
            'last_donation_date': last_donation_date,
            'weight':             weight_val,
        })
        flash('Donor profile updated.', 'success')
        return redirect(url_for('dashboard'))

    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    return render_template('register_donor.html',
                           donor=donor,
                           blood_groups=blood_groups,
                           states_list=INDIA_LOCATIONS.keys())

@app.route('/dashboard/delete-donor', methods=['POST'])
@login_required
def delete_donor():
    uid   = session['user_id']
    donor = fs_get_donor_by_user(uid)
    if donor:
        donors_col.document(donor['id']).delete()
        flash('Your donor profile has been deleted.', 'info')
    return redirect(url_for('dashboard'))

# ─── Emergency Requests ───────────────────────────────────────────────────────

@app.route('/emergency', methods=['GET', 'POST'])
def emergency():
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to submit emergency requests.', 'warning')
            return redirect(url_for('login', next=url_for('emergency')))

        patient_name     = request.form.get('patient_name', '').strip()
        blood_group      = request.form.get('blood_group', '')
        units_needed     = request.form.get('units_needed', '')
        hospital_name    = request.form.get('hospital_name', '').strip()
        state            = request.form.get('state', '')
        city             = request.form.get('city', '')
        contact_phone    = request.form.get('contact_phone', '').strip()
        description      = request.form.get('description', '').strip()
        required_by_str  = request.form.get('required_by', '')

        if not all([patient_name, blood_group, hospital_name, state, city, contact_phone, units_needed, required_by_str]):
            flash('All marked fields are required.', 'danger')
            return redirect(url_for('emergency'))

        try:
            units = int(units_needed)
            if units <= 0:
                raise ValueError
        except ValueError:
            flash('Units must be a positive number.', 'danger')
            return redirect(url_for('emergency'))

        try:
            datetime.strptime(required_by_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('emergency'))

        # Notify matching available donors
        matching_donors = fs_query_donors(blood_group=blood_group, city=city)
        for d in matching_donors:
            if d.get('is_available'):
                send_email_notification(
                    d.get('email', ''),
                    f"URGENT: {blood_group} Blood Needed in {city}!",
                    f"Dear {d.get('name')},\n\nEmergency blood request for {patient_name} needing "
                    f"{units} units of {blood_group} blood at {hospital_name}, {city}, {state}.\n"
                    f"Required By: {required_by_str}\nContact Phone: {contact_phone}\n\n"
                    f"Best Regards,\nLifeLink Team"
                )

        requests_col.document(str(uuid.uuid4())).set({
            'patient_name':  patient_name,
            'blood_group':   blood_group,
            'hospital_name': hospital_name,
            'city':          city,
            'state':         state,
            'contact_name':  'Contact Person',
            'contact_phone': contact_phone,
            'units_needed':  units,
            'required_by':   required_by_str,
            'description':   description,
            'is_fulfilled':  False,
            'created_at':    firestore.SERVER_TIMESTAMP,
        })
        flash('Emergency blood request submitted!', 'success')
        return redirect(url_for('emergency'))

    requests_list = fs_get_active_requests()
    blood_groups  = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    return render_template('emergency.html',
                           requests=requests_list,
                           blood_groups=blood_groups,
                           states_list=INDIA_LOCATIONS.keys())

# ─── Admin Dashboard ─────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin():
    users_list    = fs_get_all_users()
    donors_list   = fs_get_all_donors()
    requests_list = fs_get_all_requests()

    blood_groups   = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    total_users    = len(users_list)
    total_donors   = len(donors_list)
    active_requests = sum(1 for r in requests_list if not r.get('is_fulfilled'))

    return render_template('admin.html',
                           total_users=total_users,
                           total_donors=total_donors,
                           active_requests=active_requests,
                           users=users_list,
                           donors=donors_list,
                           requests=requests_list,
                           blood_groups=blood_groups,
                           states_list=INDIA_LOCATIONS.keys(),
                           current_username=session.get('admin_username', 'Admin'))

@app.route('/admin/donor/<string:donor_id>/edit', methods=['POST'])
@admin_required
def admin_edit_donor(donor_id):
    donor = fs_get_donor_by_id(donor_id)
    if not donor:
        flash('Donor not found.', 'danger')
        return redirect(url_for('admin'))

    last_donation_str = request.form.get('last_donation_date', '')
    last_donation_date = None
    if last_donation_str:
        try:
            datetime.strptime(last_donation_str, '%Y-%m-%d')
            last_donation_date = last_donation_str
        except ValueError:
            pass

    donors_col.document(donor_id).update({
        'name':               request.form.get('name', '').strip(),
        'age':                int(request.form.get('age', 25)),
        'gender':             request.form.get('gender', ''),
        'blood_group':        request.form.get('blood_group', ''),
        'phone':              request.form.get('phone', '').strip(),
        'email':              request.form.get('email', '').strip(),
        'state':              request.form.get('state', ''),
        'city':               request.form.get('city', ''),
        'last_donation_date': last_donation_date,
        'is_available':       'is_available' in request.form,
        'weight':             float(request.form.get('weight', 55)),
    })
    flash('Donor updated successfully.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/donor/<string:donor_id>/delete', methods=['POST'])
@admin_required
def admin_delete_donor(donor_id):
    donors_col.document(donor_id).delete()
    flash('Donor profile deleted.', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/request/<string:req_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_request(req_id):
    req = fs_get_request_by_id(req_id)
    if req:
        requests_col.document(req_id).update({'is_fulfilled': not req.get('is_fulfilled', False)})
        flash('Blood request fulfillment status updated.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/request/<string:req_id>/delete', methods=['POST'])
@admin_required
def admin_delete_request(req_id):
    requests_col.document(req_id).delete()
    flash('Emergency blood request deleted.', 'info')
    return redirect(url_for('admin'))

@app.route('/admin/user/<string:user_id>/toggle-admin', methods=['POST'])
@admin_required
def admin_toggle_user_admin(user_id):
    if user_id == session['user_id']:
        flash('You cannot revoke admin privileges from yourself.', 'danger')
        return redirect(url_for('admin'))

    user = fs_get_user_by_id(user_id)
    if user:
        users_col.document(user_id).update({'is_admin': not user.get('is_admin', False)})
        flash('User role updated successfully.', 'success')
    return redirect(url_for('admin'))

# ─── Startup Info ─────────────────────────────────────────────────────────────

print("---------------------------------------------------------")
print("LifeLink running in FIREBASE FIRESTORE persistence mode.")
print("Project ID: lifelink-e1484")
print("To test the Admin dashboard, log in with:")
print(">> Email: admin@lifelink.org  |  Password: admin123")
print("To test the Donor dashboard, log in with:")
print(">> Email: john@gmail.com      |  Password: password123")
print("---------------------------------------------------------")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

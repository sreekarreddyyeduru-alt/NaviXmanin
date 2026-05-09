"""Authentication blueprint."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
import hashlib, secrets, time

# template_folder='.' so auth blueprint also finds templates in root
auth_bp = Blueprint('auth', __name__, template_folder='.')
USERS = {}
RESET_CODES = {}

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('user_email'):
            flash('Please log in to access that page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return wrapper

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        user = USERS.get(email)
        if not user or user['password_hash'] != _hash(password):
            flash('Invalid email or password.', 'error')
            return render_template('login.html')
        session['user_email'] = email
        session['user_name'] = user['name']
        flash(f"Welcome back, {user['name']}!", 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('signup.html')
        if email in USERS:
            flash('An account with that email already exists.', 'error')
            return render_template('signup.html')
        USERS[email] = {'name':name,'password_hash':_hash(password),'created_at':time.time()}
        session['user_email'] = email
        session['user_name'] = name
        session['subscription_plan'] = 'free'
        flash(f'Welcome to NaviX, {name}!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('forgot.html')
        RESET_CODES[email] = {'code':'123456','expires':time.time()+3600}
        session['reset_email'] = email
        flash('Reset code sent! Use 123456 for demo.', 'success')
        return redirect(url_for('auth.reset'))
    return render_template('forgot.html')

@auth_bp.route('/reset', methods=['GET','POST'])
def reset():
    if request.method == 'POST':
        email = session.get('reset_email')
        code = request.form.get('code','').strip()
        new_password = request.form.get('password','')
        if not email:
            flash('Please request a reset code first.', 'error')
            return redirect(url_for('auth.forgot'))
        record = RESET_CODES.get(email)
        if not record or record['code'] != code or record['expires'] < time.time():
            flash('Invalid or expired reset code.', 'error')
            return render_template('reset.html')
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('reset.html')
        if email not in USERS:
            USERS[email] = {'name':email.split('@')[0].title(),'password_hash':_hash(new_password),'created_at':time.time()}
        else:
            USERS[email]['password_hash'] = _hash(new_password)
        del RESET_CODES[email]
        session.pop('reset_email', None)
        flash('Password reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset.html')

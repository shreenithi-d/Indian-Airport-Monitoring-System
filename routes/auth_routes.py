from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, limiter
from models import User
from utils.validators import validate_email, validate_phone
import re

auth_bp = Blueprint('auth', __name__)

def validate_password_strength(password):
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter.'
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one digit.'
    return True, ''

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('10 per minute')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        errors = []
        if not name or len(name) < 2:
            errors.append('Full name must be at least 2 characters.')
        if not validate_email(email):
            errors.append('Please enter a valid email address.')
        if phone and not validate_phone(phone):
            errors.append('Please enter a valid phone number.')
        valid_pw, pw_msg = validate_password_strength(password)
        if not valid_pw:
            errors.append(pw_msg)
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('register.html', name=name, email=email, phone=phone)
        
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email address already exists. Please sign in.', 'warning')
            return render_template('register.html')
        
        user = User(name=name, email=email, phone=phone or None, role='user', is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'Welcome, {name}! Your account has been created.', 'success')
        return redirect(url_for('dashboard.index'))
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('20 per minute')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please enter your email and password.', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', email=email)
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'warning')
            return render_template('login.html')
        
        login_user(user, remember=bool(remember))
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        
        if user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('dashboard.index'))
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

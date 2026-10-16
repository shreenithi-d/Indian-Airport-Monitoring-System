from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User
from models.audit_log import AuditLog
from utils.validators import validate_email_format, validate_password_strength
from utils.helpers import is_safe_url

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('airports.map_view'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone_number = request.form.get('phone_number', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not full_name or not email or not password:
            flash("Please fill in all required fields.", "danger")
            return render_template('register.html')

        if not validate_email_format(email):
            flash("Please enter a valid email address.", "danger")
            return render_template('register.html')

        valid_pass, pass_msg = validate_password_strength(password)
        if not valid_pass:
            flash(pass_msg, "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        # Check existing user
        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists.", "warning")
            return render_template('register.html')

        # Create user
        user = User(
            full_name=full_name,
            email=email,
            phone_number=phone_number,
            role='passenger',
            account_status='active'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        audit = AuditLog(
            actor_user_id=user.id,
            action='USER_REGISTER',
            entity_type='User',
            entity_id=user.id,
            notes=f"New user registered: {user.email}"
        )
        db.session.add(audit)
        db.session.commit()

        login_user(user)
        flash("Registration successful! Welcome to Indian Airport Monitoring System.", "success")
        return redirect(url_for('airports.map_view'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('airports.map_view'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template('login.html')

        if user.account_status != 'active':
            flash("Your account has been suspended. Please contact the administrator.", "danger")
            return render_template('login.html')

        login_user(user, remember=remember)

        # Audit login
        audit = AuditLog(
            actor_user_id=user.id,
            action='USER_LOGIN',
            entity_type='User',
            entity_id=user.id,
            notes=f"User logged in from {request.remote_addr}"
        )
        db.session.add(audit)
        db.session.commit()

        next_page = request.args.get('next')
        if next_page and is_safe_url(next_page):
            return redirect(next_page)

        if user.is_admin:
            flash(f"Welcome back, Administrator {user.full_name}!", "info")
            return redirect(url_for('admin.dashboard'))
        else:
            flash(f"Welcome back, {user.full_name}!", "success")
            return redirect(url_for('airports.map_view'))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    audit = AuditLog(
        actor_user_id=current_user.id,
        action='USER_LOGOUT',
        entity_type='User',
        entity_id=current_user.id,
        notes="User logged out."
    )
    db.session.add(audit)
    db.session.commit()
    logout_user()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('main.landing'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            full_name = request.form.get('full_name', '').strip()
            phone = request.form.get('phone_number', '').strip()
            if full_name:
                current_user.full_name = full_name
                current_user.phone_number = phone
                db.session.commit()
                flash("Profile details updated successfully.", "success")
        elif action == 'change_password':
            old_pass = request.form.get('old_password', '')
            new_pass = request.form.get('new_password', '')
            confirm_new = request.form.get('confirm_new_password', '')

            if not current_user.check_password(old_pass):
                flash("Current password is incorrect.", "danger")
            elif new_pass != confirm_new:
                flash("New passwords do not match.", "danger")
            else:
                valid_pass, msg = validate_password_strength(new_pass)
                if not valid_pass:
                    flash(msg, "danger")
                else:
                    current_user.set_password(new_pass)
                    db.session.commit()
                    flash("Password changed successfully.", "success")

    user_bookings = current_user.bookings.order_by(db.desc('created_at')).limit(5).all()
    return render_template('profile.html', user=current_user, recent_bookings=user_bookings)

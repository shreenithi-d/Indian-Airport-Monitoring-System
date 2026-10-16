from models.user import User

def test_user_registration_success(client, app):
    response = client.post('/register', data={
        'full_name': 'New Traveler',
        'email': 'newtraveler@test.com',
        'phone_number': '+91 91234 56789',
        'password': 'Secure@Password123',
        'confirm_password': 'Secure@Password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='newtraveler@test.com').first()
        assert user is not None
        assert user.full_name == 'New Traveler'
        assert user.check_password('Secure@Password123')
        assert user.role == 'passenger'

def test_duplicate_registration_rejection(client, app):
    # passenger@test.com already seeded in conftest
    response = client.post('/register', data={
        'full_name': 'Duplicate User',
        'email': 'passenger@test.com',
        'phone_number': '+91 99999 00000',
        'password': 'Password123',
        'confirm_password': 'Password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"already exists" in response.data

def test_login_success_and_logout(client):
    # Test valid login
    response = client.post('/login', data={
        'email': 'passenger@test.com',
        'password': 'Pass@123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back" in response.data

    # Test logout
    logout_res = client.get('/logout', follow_redirects=True)
    assert logout_res.status_code == 200
    assert b"successfully logged out" in logout_res.data

def test_login_incorrect_password(client):
    response = client.post('/login', data={
        'email': 'passenger@test.com',
        'password': 'WrongPassword123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid email or password" in response.data

def test_admin_access_restrictions(client):
    # Log in as normal passenger
    client.post('/login', data={
        'email': 'passenger@test.com',
        'password': 'Pass@123'
    }, follow_redirects=True)

    # Attempt accessing admin dashboard -> should return 403 Forbidden
    response = client.get('/admin/dashboard')
    assert response.status_code == 403

def test_admin_access_allowed(client):
    # Log in as admin
    client.post('/login', data={
        'email': 'admin@test.com',
        'password': 'Admin@123'
    }, follow_redirects=True)

    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b"Operations Command Center" in response.data

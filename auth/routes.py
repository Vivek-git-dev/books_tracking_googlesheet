from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from config import Config
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check against environment variables
        if username == Config.AUTH_USERNAME and password == Config.AUTH_PASSWORD:
            user = User(Config.AUTH_USERNAME)
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Registration disabled - user is configured via environment variables
    flash('Registration is disabled. Please use the configured credentials.')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

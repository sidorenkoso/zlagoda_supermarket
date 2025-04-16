from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Employee, db
from datetime import datetime
from . import views

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()
        user = Employee.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):  # Перевіряємо хешований пароль
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))  # Перенаправляємо на головну сторінку
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@views.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

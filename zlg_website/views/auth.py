import sqlite3
from werkzeug.security import check_password_hash
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from datetime import datetime
from . import views

# Імпровізований об'єкт-клас для сумісності з Flask-Login
class Employee(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip()
        password = request.form.get('password').strip()

        # Підключення до БД
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()

        # Отримання користувача за email
        cursor.execute("SELECT id, email, password FROM employee WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()

        if row:
            user_id, user_email, hashed_password = row
            if check_password_hash(hashed_password, password):
                user = Employee(user_id, user_email, hashed_password)
                login_user(user, remember=True)
                flash('Logged in successfully!', category='success')
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@views.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('views.login'))  # або 'auth.login', якщо так названий Blueprint
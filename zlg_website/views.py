from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    # Відображати сторінку головна (main.html)
    return render_template("main.html", user=current_user)


@views.route('/welcome')
@login_required
def welcome():
    # Відображати сторінку привітання (home.html)
    return render_template("home.html", user=current_user)


@views.route('/employees')
@login_required
def employees():
    # Тут у реальному додатку ви б отримували дані про працівників з бази даних
    # Приклад:
    employees = []  # Замість цього буде щось типу Employee.query.all()

    return render_template("employees.html", user=current_user, employees=employees)


# Можна також додати додаткові маршрути для деталей, редагування, видалення і додавання працівників
@views.route('/employees/add')
@login_required
def add_employee():
    return "Сторінка додавання працівника буде тут"  # Замініть на відповідний шаблон


@views.route('/employees/<int:id>')
@login_required
def employee_details(id):
    return f"Деталі працівника з ID {id}"  # Замініть на відповідний шаблон


@views.route('/employees/edit/<int:id>')
@login_required
def edit_employee(id):
    return f"Редагування працівника з ID {id}"  # Замініть на відповідний шаблон


@views.route('/employees/delete/<int:id>')
@login_required
def delete_employee(id):
    return f"Видалення працівника з ID {id}"  # Додайте логіку видалення
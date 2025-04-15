from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Employee, db
from datetime import datetime

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
    if current_user.position != 'Менеджер':
        abort(403)
    role_filter = request.args.get('position')  # 'Касир' або 'Менеджер'
    if role_filter:
        all_employees = Employee.query.filter_by(position=role_filter).order_by(Employee.id).all()
    else:
        all_employees = Employee.query.order_by(Employee.id).all()

    return render_template("employees.html", user=current_user, employees=all_employees, current_filter=role_filter)


# Оновлені маршрути для додавання працівників
@views.route('/employees/add', methods=['GET'])
@login_required
def add_employee_form():
    if current_user.position != 'Менеджер':
        abort(403)  # Тільки менеджери можуть додавати працівників
    return render_template("add_employee.html", user=current_user)


@views.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
    if current_user.position != 'Менеджер':
        abort(403)

    if request.method == "POST":
        try:
            # Отримуємо дані з форми
            id = request.form.get("id")
            full_name = request.form.get("full_name")
            position = request.form.get("position")
            salary = request.form.get("salary")
            birth_date = datetime.strptime(request.form.get("birth_date"), "%Y-%m-%d")
            start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
            phone = request.form.get("phone")
            address = request.form.get("address")
            email = request.form.get("email")
            password = request.form.get("password")  # В реальному додатку тут має бути хешування паролю

            # Створюємо нового працівника
            new_employee = Employee(
                id=id,
                full_name=full_name,
                position=position,
                salary=salary,
                birth_date=birth_date,
                start_date=start_date,
                phone=phone,
                address=address,
                email=email,
                password=password  # В реальному додатку тут має бути хешований пароль
            )

            # Додаємо в базу даних
            db.session.add(new_employee)
            db.session.commit()

            flash("Працівника успішно додано!", "success")
            return redirect(url_for("views.employees"))

        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при додаванні працівника: {str(e)}", "error")
            return redirect(url_for("views.add_employee_form"))


@views.route('/employees/<int:id>')
@login_required
def employee_details(id):
    return f"Деталі працівника з ID {id}"  # Замініть на відповідний шаблон


@views.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    if current_user.position != 'Менеджер':
        abort(403)

    employee = Employee.query.get_or_404(id)

    if request.method == 'POST':
        try:
            employee.full_name = request.form.get("full_name")
            employee.position = request.form.get("position")
            employee.salary = float(request.form.get("salary"))
            employee.birth_date = datetime.strptime(request.form.get("birth_date"), "%Y-%m-%d")
            employee.start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
            employee.phone = request.form.get("phone")
            employee.address = request.form.get("address")
            employee.email = request.form.get("email")

            new_password = request.form.get("password")
            if new_password:
                employee.password = new_password  # ⚠️ в реальній системі хешуй пароль

            db.session.commit()
            flash("Зміни збережено успішно!", "success")
            return redirect(url_for('views.employees'))
        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при оновленні: {str(e)}", "error")
            return redirect(url_for('views.edit_employee', id=id))

    return render_template("edit_employee.html", user=current_user, employee=employee)



@views.route('/employees/delete/<int:id>')
@login_required
def delete_employee(id):
    return f"Видалення працівника з ID {id}"  # Додайте логіку видалення

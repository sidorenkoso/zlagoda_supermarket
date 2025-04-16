from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Employee, db
from datetime import datetime
from . import views

# Оновлені маршрути для додавання працівників
@views.route('/employees/add', methods=['GET'])
@login_required
def add_employee_form():
    if current_user.position != 'Менеджер':
        abort(403)  # Тільки менеджери можуть додавати працівників

    try:
        last_employee = db.session.query(Employee).order_by(Employee.id.desc()).first()
        next_id = (last_employee.id + 1) if last_employee else 1
    except Exception as e:
        next_id = 1  # якщо база ще пуста або сталася помилка

    return render_template("add_employee.html", user=current_user, next_id=next_id)



@views.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
    if current_user.position != 'Менеджер':
        abort(403)

    if request.method == "POST":
        try:
            # Отримуємо дані з форми
            id = int(request.form.get("id"))
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

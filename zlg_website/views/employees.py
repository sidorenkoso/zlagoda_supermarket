from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from zlg_website.models import Employee, db
from datetime import datetime
from . import views
from sqlalchemy import func

@views.route('/employees')
@login_required
def employees():
    if current_user.position != 'Менеджер':
        abort(403)

    search_query = request.args.get('search', '')
    position_filter = request.args.get('position')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    query = Employee.query

    if position_filter:
        query = query.filter(Employee.position == position_filter)

    # Сортування
    if sort == 'last_name':
        if order == 'desc':
            query = query.order_by(Employee.last_name.desc())
        else:
            query = query.order_by(Employee.last_name.asc())
    else:
        query = query.order_by(Employee.id.asc())  # за замовчуванням

    employees = query.all()

    if search_query:
        search_lower = search_query.lower()
        employees = [
            emp for emp in employees
            if emp.last_name and emp.last_name.lower().startswith(search_lower)
        ]

    return render_template("employees.html", user=current_user, employees=employees, current_filter=position_filter)


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

    return render_template("form_employees.html", user=current_user, next_id=next_id)



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
            today = datetime.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

            if age < 18:
                flash("Працівнику має бути не менше 18 років!", "error")
                return redirect(url_for("views.add_employee_form"))
            start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
            phone = request.form.get("phone")
            address = request.form.get("address")
            email = request.form.get("email")
            password = generate_password_hash(request.form.get("password"))

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
                password=password
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

    return render_template("form_employees.html", user=current_user, employee=employee)



@views.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    if current_user.position != 'Менеджер':
        abort(403)

    employee = Employee.query.get_or_404(id)

    try:
        db.session.delete(employee)
        db.session.commit()
        flash("Працівника успішно видалено!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Помилка при видаленні: {str(e)}", "error")

    return redirect(url_for('views.employees'))
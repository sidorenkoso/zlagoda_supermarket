from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Employee, db
from datetime import datetime
from . import views

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
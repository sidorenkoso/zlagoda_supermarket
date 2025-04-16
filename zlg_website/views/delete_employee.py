from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Employee, db
from datetime import datetime
from . import views

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
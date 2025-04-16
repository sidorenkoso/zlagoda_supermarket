from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Employee, db
from datetime import datetime
from . import views

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

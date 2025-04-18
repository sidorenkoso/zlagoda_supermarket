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

    search_query = request.args.get('search', '')
    position_filter = request.args.get('position')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    query = Employee.query

    if position_filter:
        query = query.filter(Employee.position == position_filter)

    if search_query:
        query = query.filter(Employee.last_name.ilike(f"%{search_query}%"))

    # Сортування
    if sort == 'last_name':
        if order == 'desc':
            query = query.order_by(Employee.last_name.desc())
        else:
            query = query.order_by(Employee.last_name.asc())
    else:
        query = query.order_by(Employee.id.asc())  # за замовчуванням

    employees = query.all()

    return render_template("employees.html", user=current_user, employees=employees, current_filter=position_filter)

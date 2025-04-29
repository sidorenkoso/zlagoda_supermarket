from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Receipt, Employee, db
from datetime import datetime, timedelta
from . import views


@views.route('/receipts')
@login_required
def receipts():
    # Отримуємо параметри фільтрації
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    sort = request.args.get('sort', 'date')
    order = request.args.get('order', 'desc')

    # Базовий запит
    query = Receipt.query
    if current_user.position == 'Касир':
        query = query.filter(Receipt.employee_id == current_user.id)
    elif employee_id:
        query = query.filter(Receipt.employee_id == employee_id)

    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Receipt.date >= date_from)

    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        # Додаємо один день, щоб включити весь вибраний день
        date_to = date_to + timedelta(days=1)
        query = query.filter(Receipt.date < date_to)

    # Застосовуємо сортування
    if sort == 'receipt_number':
        if order == 'asc':
            query = query.order_by(Receipt.receipt_number.asc())
        else:
            query = query.order_by(Receipt.receipt_number.desc())
    elif sort == 'date':
        if order == 'asc':
            query = query.order_by(Receipt.date.asc())
        else:
            query = query.order_by(Receipt.date.desc())

    # Виконуємо запит
    receipts = query.all()

    # Розраховуємо загальну суму всіх відфільтрованих чеків
    total_sum = sum(receipt.total_sum for receipt in receipts)

    # Отримуємо всіх працівників для випадаючого списку
    employees = Employee.query.all()

    return render_template(
        'receipts.html',
        user=current_user,
        receipts=receipts,
        employees=employees,
        total_sum=total_sum
    )


@views.route('/view_receipt/<receipt_number>')
@login_required
def view_receipt(receipt_number):
    # Отримуємо чек за його номером
    receipt = Receipt.query.get_or_404(receipt_number)
    return render_template('receipts_items.html', receipt=receipt,
        user=current_user)


@views.route('/delete_receipt/<receipt_number>', methods=['POST'])
@login_required
def delete_receipt(receipt_number):
    receipt = Receipt.query.get_or_404(receipt_number)

    # Видаляємо всі пов'язані позиції чеку спочатку
    for item in receipt.items:
        db.session.delete(item)

    # Потім видаляємо сам чек
    db.session.delete(receipt)
    db.session.commit()

    flash('Чек успішно видалено', 'success')
    return redirect(url_for('views.receipts'),
        user=current_user)
from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, jsonify
from flask_login import login_required, current_user
from zlg_website.models import Receipt, Employee, db, CustomerCard, Product, StoreProduct
from datetime import datetime, timedelta
from . import views
import re


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
    if sort == 'date':
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
        total_sum=total_sum,
        sort=sort,
        order=order
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


@views.route('/receipts/add', methods=['GET', 'POST'])
@login_required
def add_receipts():
    if current_user.position != 'Касир':
        abort(403)

    new_receipt_number = generate_receipt_number()  # ← ТЕПЕР ЦЕ ЗА МЕЖАМИ if

    if request.method == "POST":
        try:
            card_number = request.form.get('card_number') or None
            print_date = datetime.now()

            new_receipt = Receipt(
                receipt_number=new_receipt_number,
                employee_id=current_user.id,
                card_number=card_number,
                print_date=print_date
            )

            db.session.add(new_receipt)
            db.session.commit()

            flash("Чек успішно додано!", "success")
            return redirect(url_for("views.receipts"))

        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при додаванні чеку: {str(e)}", "error")

    return render_template("add_receipt.html", user=current_user, receipt_number=new_receipt_number)



def generate_receipt_number():
    # Отримуємо останній чек за номером (за спаданням)
    last_receipt = Receipt.query.order_by(Receipt.receipt_number.desc()).first()

    if last_receipt:
        # Витягуємо числову частину з формату R8613
        match = re.search(r'R(\d+)', last_receipt.receipt_number)
        if match:
            number = int(match.group(1)) + 1
        else:
            number = 1
    else:
        number = 1

    # Формуємо новий номер чеку: R8614
    return f'R{number}'


@views.route('/api/client_info')
@login_required
def get_client_info():
    card_number = request.args.get('card_number')

    if not card_number:
        return jsonify({'error': 'Номер картки не вказано'}), 400

    client = CustomerCard.query.filter_by(card_number=card_number).first()
    if not client:
        return jsonify({'error': 'Клієнта не знайдено'}), 404

    return jsonify({
        'full_name': f"{client.last_name} {client.first_name} {client.middle_name or ''}".strip(),
        'discount_percent': client.discount_percent
    })



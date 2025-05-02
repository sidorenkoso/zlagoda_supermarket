from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, jsonify
from flask_login import login_required, current_user
from zlg_website import db
from datetime import datetime, timedelta
from sqlalchemy import text
from . import views
import re
from flask_login import UserMixin
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.sql import text
from ..models import Receipt


# Ваша функція для отримання чеків
@views.route('/receipts')
@login_required
def receipts():
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    sort = request.args.get('sort', 'date')
    order = request.args.get('order', 'desc')

    filters = []
    params = {}

    if current_user.position == 'Касир':
        filters.append("r.employee_id = :user_id")
        params['user_id'] = current_user.id
    elif employee_id:
        filters.append("r.employee_id = :employee_id")
        params['employee_id'] = employee_id

    if date_from:
        filters.append("r.date >= :date_from")
        params['date_from'] = date_from

    if date_to:
        date_to_dt = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        filters.append("r.date < :date_to")
        params['date_to'] = date_to_dt.strftime('%Y-%m-%d')

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    query_str = f"""
        SELECT r.receipt_number, r.date, e.first_name AS employee_first_name, e.last_name AS employee_last_name
        FROM Receipt r
        JOIN Employee e ON r.employee_id = e.id
        {where_clause}
        ORDER BY r.date {'ASC' if order == 'asc' else 'DESC'}
    """

    # Отримуємо всі чеки
    receipts = Receipt.get_all()

    # Для кожного чеку обчислюємо total_sum і vat
    for receipt in receipts:
        receipt.total_sum = receipt.get_total_sum()
        receipt.vat = receipt.get_vat()

        # Переконатися, що `receipt.date` є об'єктом datetime
        if isinstance(receipt.date, str):
            receipt.date = datetime.strptime(receipt.date, '%Y-%m-%d')

    # Загальна сума всіх чеків
    total_sum = sum(r.total_sum for r in receipts)

    employees = db.session.execute(text("SELECT * FROM Employee")).mappings().all()

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
    query = text("""
        SELECT * FROM Receipt WHERE receipt_number = :receipt_number
    """)
    result = db.session.execute(query, {'receipt_number': receipt_number}).mappings().first()
    if not result:
        abort(404)
    return render_template('receipts_items.html', receipt=result, user=current_user)

@views.route('/delete_receipt/<receipt_number>', methods=['POST'])
@login_required
def delete_receipt(receipt_number):
    try:
        db.session.execute(text("DELETE FROM ReceiptItem WHERE receipt_number = :receipt_number"),
                           {'receipt_number': receipt_number})
        db.session.execute(text("DELETE FROM Receipt WHERE receipt_number = :receipt_number"),
                           {'receipt_number': receipt_number})
        db.session.commit()
        flash('Чек успішно видалено', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Помилка при видаленні чеку: {str(e)}', 'danger')

    return redirect(url_for('views.receipts'))

def generate_receipt_number():
    query = text("""
        SELECT receipt_number FROM Receipt
        ORDER BY CAST(SUBSTR(receipt_number, 2) AS INTEGER) DESC
        LIMIT 1
    """)
    result = db.session.execute(query).scalar()
    if result and re.match(r'R\d+', result):
        next_num = int(result[1:]) + 1
    else:
        next_num = 1
    return f'R{next_num}'

@views.route('/api/client_info')
@login_required
def get_client_info():
    card_number = request.args.get('card_number')
    if not card_number:
        return jsonify({'error': 'Номер картки не вказано'}), 400

    client = db.session.execute(text("""
        SELECT * FROM CustomerCard WHERE card_number = :card_number
    """), {'card_number': card_number}).mappings().first()

    if not client:
        return jsonify({'error': 'Клієнта не знайдено'}), 404

    full_name = f"{client['last_name']} {client['first_name']} {client['middle_name'] or ''}".strip()
    return jsonify({'full_name': full_name, 'discount_percent': client['discount_percent']})

@views.route('/search-product')
@login_required
def search_product():
    query = request.args.get('query', '')
    if query:
        results = db.session.execute(text("""
            SELECT name FROM Product WHERE name ILIKE :query
        """), {'query': f'%{query}%'}).scalars().all()
        return jsonify([{'name': name} for name in results])
    return jsonify([])

@views.route('/api/product_info')
@login_required
def product_info():
    name = request.args.get('name')
    product = db.session.execute(text("""
        SELECT sp.upc, p.name, sp.selling_price, sp.promotional_product, sp.promo_price
        FROM StoreProduct sp
        JOIN Product p ON sp.id_product = p.id_product
        WHERE p.name = :name
    """), {'name': name}).mappings().first()

    if not product:
        return jsonify(None)

    price = product['promo_price'] if product['promotional_product'] else product['selling_price']
    return jsonify({'upc': product['upc'], 'name': product['name'], 'price': price})

@views.route('/receipts/add', methods=['GET', 'POST'])
@login_required
def add_receipts():
    if current_user.position != 'Касир':
        abort(403)

    if request.method == 'POST':
        try:
            data = request.get_json()
            card_number = data.get('card_number')
            items = data.get('items', [])

            receipt_number = generate_receipt_number()
            now = datetime.now()

            db.session.execute(text("""
                INSERT INTO Receipt (receipt_number, employee_id, customer_card_number, date)
                VALUES (:receipt_number, :employee_id, :card_number, :date)
            """), {
                'receipt_number': receipt_number,
                'employee_id': current_user.id,
                'card_number': card_number or None,
                'date': now
            })

            for item in items:
                upc = item['upc']
                quantity = int(item['quantity'])

                stock = db.session.execute(text("""
                    SELECT quantity FROM StoreProduct WHERE upc = :upc
                """), {'upc': upc}).scalar()

                if stock is None or stock < quantity:
                    raise ValueError(f"Недостатньо товару для UPC: {upc}")

                db.session.execute(text("""
                    INSERT INTO ReceiptItem (receipt_number, upc, quantity)
                    VALUES (:receipt_number, :upc, :quantity)
                """), {
                    'receipt_number': receipt_number,
                    'upc': upc,
                    'quantity': quantity
                })

                db.session.execute(text("""
                    UPDATE StoreProduct SET quantity = quantity - :qty WHERE upc = :upc
                """), {'qty': quantity, 'upc': upc})

            db.session.commit()
            return jsonify({'success': True, 'receipt_number': receipt_number})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    return render_template("add_receipt.html", user=current_user, receipt_number=generate_receipt_number())

from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, jsonify
from flask_login import login_required, current_user
from zlg_website import db
from . import views
import re
from flask_login import UserMixin
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import text
from ..models import Receipt


@views.route('/receipts')
@login_required
def receipts():
    # Існуючі параметри
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    sort = request.args.get('sort', 'date')
    order = request.args.get('order', 'desc')

    # Новий параметр пошуку за номером чеку
    search_query = request.args.get('search', '').strip()

    # Імена таблиць
    receipt_table = 'receipt'
    employee_table = 'employee'
    receiptitem_table = 'receipt_item'
    storeproduct_table = 'store_product'

    # Базовий SELECT ... FROM ... JOIN
    query_parts = [
        "SELECT r.receipt_number, r.date, r.customer_card_number, "
        "e.first_name, e.last_name, e.id as employee_id"
    ]
    query_parts.append(f"FROM {receipt_table} r")
    query_parts.append(f"JOIN {employee_table} e ON r.employee_id = e.id")

    # WHERE
    where_conditions = []
    params = {}

    # Фільтр по ролі / виборі касира
    if current_user.position == 'Касир':
        where_conditions.append("r.employee_id = :user_id")
        params['user_id'] = current_user.id
    elif employee_id:
        where_conditions.append("r.employee_id = :employee_id")
        params['employee_id'] = employee_id

    # Фільтр по датах
    if date_from:
        where_conditions.append("DATE(r.date) >= DATE(:date_from)")
        params['date_from'] = date_from
    if date_to:
        where_conditions.append("DATE(r.date) <= DATE(:date_to)")
        params['date_to'] = date_to

    # **Новий фільтр по номеру чеку**
    if search_query:
        where_conditions.append("r.receipt_number LIKE :search_query")
        # startswith — будуємо шаблон "R8374%" (можна й рівність, якщо потребуєте точний збіг)
        params['search_query'] = f"{search_query}%"

    if where_conditions:
        query_parts.append("WHERE " + " AND ".join(where_conditions))

    # ORDER BY
    sort_field = "r.date" if sort == 'date' else sort
    sort_direction = "ASC" if order == 'asc' else "DESC"
    query_parts.append(f"ORDER BY {sort_field} {sort_direction}")

    # Збираємо і виконуємо
    main_query = " ".join(query_parts)
    receipts_data = db.session.execute(text(main_query), params).mappings().all()

    # Обробка результатів, як було
    receipts = []
    total_sum = 0
    for r in receipts_data:
        items_query = text(f"""
            SELECT ri.upc, ri.quantity,
                   CASE WHEN sp.is_promotional THEN sp.promo_price ELSE sp.price END AS price
            FROM {receiptitem_table} ri
            JOIN {storeproduct_table} sp ON ri.upc = sp.upc
            WHERE ri.receipt_number = :receipt_number
        """)
        items = db.session.execute(items_query, {'receipt_number': r['receipt_number']}).mappings().all()
        receipt_total = sum(item['price'] * item['quantity'] for item in items) if items else 0
        total_sum += receipt_total
        receipts.append({
            'receipt_number': r['receipt_number'],
            'date': r['date'],
            'total_sum': receipt_total,
            'vat': receipt_total * 0.2,
            'employee': {
                'id': r['employee_id'],
                'first_name': r['first_name'],
                'last_name': r['last_name'],
            }
        })

    # Список касирів для фільтру
    employees = db.session.execute(text(f"SELECT * FROM {employee_table}")).mappings().all()

    return render_template(
        'receipts.html',
        user=current_user,
        receipts=receipts,
        employees=employees,
        total_sum=total_sum,
        sort=sort,
        order=order,
        # передамо назад, щоб в полях залишилось значення
        search_query=search_query,
        employee_id=employee_id,
        date_from=date_from,
        date_to=date_to
    )



@views.route('/view_receipt/<receipt_number>')
@login_required
def view_receipt(receipt_number):
    # Отримуємо чек з інформацією про працівника і клієнта
    receipt_query = text("""
        SELECT r.*, 
               e.last_name AS employee_last_name, e.first_name AS employee_first_name,
               cc.last_name AS customer_card_last_name, cc.first_name AS customer_card_first_name,
               cc.discount_percent AS customer_card_discount_percent
        FROM receipt r
        JOIN employee e ON r.employee_id = e.id
        LEFT JOIN customer_card cc ON r.customer_card_number = cc.card_number
        WHERE r.receipt_number = :receipt_number
    """)

    # Виконання запиту та отримання результату
    receipt = db.session.execute(receipt_query, {"receipt_number": receipt_number}).fetchone()
    if not receipt:
        abort(404)

    if receipt.customer_card_number is None:
        print("Немає даних по клієнту")
    else:
        print("Дані клієнта наявні")

    # Отримуємо товари у чеку
    items_query = text("""
        SELECT ri.*, sp.price AS store_product_price, p.name AS store_product_product_name, sp.is_promotional, sp.promo_price
        FROM receipt_item ri
        JOIN store_product sp ON ri.upc = sp.upc
        JOIN product p ON sp.product_id = p.id
        WHERE ri.receipt_number = :receipt_number
    """)

    # Виконання запиту для отримання товарів
    items = db.session.execute(items_query, {"receipt_number": receipt_number}).fetchall()

    # Обчислюємо total_sum і vat з перевіркою на наявність необхідних полів
    total_sum = 0
    for item in items:
        # Доступ до значень без індексації, без перевірки на наявність кожного поля
        quantity = item.quantity if item.quantity else 0
        store_product_price = item.store_product_price if item.store_product_price else 0

        # Перевірка на акційний товар
        if item.is_promotional:  # Якщо товар акційний
            store_product_price = item.promo_price if item.promo_price else store_product_price

        # Обчислення загальної суми для кожного товару
        total_sum += quantity * store_product_price

    # Обчислення ПДВ (20%)
    vat = round(total_sum * 0.2, 2)

    # Повертаємо результат в шаблон
    return render_template(
        "receipts_items.html",
        receipt=receipt,
        items=items,
        total_sum=round(total_sum, 2),
        vat=vat,
        user=current_user
    )


@views.route('/delete_receipt/<receipt_number>', methods=['POST'])
@login_required
def delete_receipt(receipt_number):
    try:
        db.session.execute(text("DELETE FROM receipt_item WHERE receipt_number = :receipt_number"),
                           {'receipt_number': receipt_number})
        db.session.execute(text("DELETE FROM receipt WHERE receipt_number = :receipt_number"),
                           {'receipt_number': receipt_number})
        db.session.commit()
        flash('Чек успішно видалено', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Помилка при видаленні чеку: {str(e)}', 'danger')

    return redirect(url_for('views.receipts'))

def generate_receipt_number():
    query = text("""
        SELECT receipt_number FROM receipt
        ORDER BY CAST(SUBSTR(receipt_number, 2) AS INTEGER) DESC
        LIMIT 1
    """)
    result = db.session.execute(query).scalar()
    if result and re.match(r'R\d+', result):
        next_num = int(result[1:]) + 1
    else:
        next_num = 1
    return f'R{next_num}'


# Виправлення для отримання інформації про клієнта
@views.route('/api/client_info')
@login_required
def get_client_info():
    card_number = request.args.get('card_number')
    if not card_number:
        return jsonify({'error': 'Номер картки не вказано'}), 400

    client = db.session.execute(text("""
        SELECT * FROM customer_card WHERE card_number = :card_number
    """), {'card_number': card_number}).mappings().first()

    if not client:
        # Замість 404 повертаємо 200 з повідомленням про помилку
        return jsonify({'error': 'Клієнта не знайдено'}), 200

    full_name = f"{client['last_name']} {client['first_name']} {client['middle_name'] or ''}".strip()
    return jsonify({'full_name': full_name, 'discount_percent': client['discount_percent']})


# Виправлення пошуку товарів
@views.route('/search-product')
@login_required
def search_product():
    query = request.args.get('query', '')

    if not query:
        return jsonify([])

    try:
        results = db.session.execute(text("""
            SELECT DISTINCT p.name 
            FROM product p
            JOIN store_product sp ON p.id = sp.product_id
            WHERE LOWER(p.name) LIKE LOWER(:query || '%')
            AND sp.quantity > 0
            LIMIT 10
        """), {'query': f'%{query}%'}).mappings().all()

        return jsonify([{'name': item['name']} for item in results])
    except Exception as e:
        print(f"Помилка пошуку товарів: {str(e)}")
        return jsonify([]), 500


# Виправлення отримання інформації про товар
@views.route('/api/product_info')
@login_required
def product_info():
    name = request.args.get('name')
    if not name:
        return jsonify(None)

    try:
        product = db.session.execute(text("""
            SELECT sp.upc, p.name, sp.price as selling_price, 
                   sp.is_promotional as promotional_product, sp.promo_price
            FROM store_product sp
            JOIN product p ON sp.product_id = p.id
            WHERE p.name = :name AND sp.quantity > 0
            LIMIT 1
        """), {'name': name}).mappings().first()

        if not product:
            return jsonify(None)

        price = product['promo_price'] if product['promotional_product'] else product['selling_price']
        return jsonify({
            'upc': product['upc'],
            'name': product['name'],
            'price': float(price)
        })
    except Exception as e:
        print(f"Помилка отримання інформації про товар: {str(e)}")
        return jsonify(None), 500


# Виправлення для додавання чеку
@views.route('/receipts/add', methods=['GET', 'POST'])
@login_required
def add_receipts():
    # Перевірка, чи користувач є касиром
    if current_user.position != 'Касир':
        abort(403)

    if request.method == 'POST':
        try:
            data = request.get_json()
            card_number = data.get('card_number')
            items = data.get('items', [])

            if not items:
                return jsonify({'success': False, 'message': 'Чек не може бути пустим'}), 400

            receipt_number = generate_receipt_number()
            now = datetime.now()

            # Перевіряємо валідність картки клієнта, якщо вона вказана
            if card_number:
                client = db.session.execute(text("""
                    SELECT card_number FROM customer_card WHERE card_number = :card_number
                """), {'card_number': card_number}).scalar()

                if not client:
                    card_number = None  # Якщо картка невалідна, не використовуємо її

            # Створюємо чек
            db.session.execute(text("""
                INSERT INTO receipt (receipt_number, employee_id, customer_card_number, date)
                VALUES (:receipt_number, :employee_id, :card_number, :date)
            """), {
                'receipt_number': receipt_number,
                'employee_id': current_user.id,
                'card_number': card_number,
                'date': now
            })

            # Додаємо товари в чек
            for item in items:
                upc = item['upc']
                quantity = int(item['quantity'])

                # Перевіряємо наявність товару
                stock_result = db.session.execute(text("""
                    SELECT quantity FROM store_product WHERE upc = :upc
                """), {'upc': upc}).scalar()

                stock = int(stock_result) if stock_result is not None else 0

                if stock < quantity:
                    raise ValueError(
                        f"Недостатньо товару на складі для UPC: {upc}. На складі: {stock}, потрібно: {quantity}")

                # Додаємо товар у чек
                db.session.execute(text("""
                    INSERT INTO receipt_item (receipt_number, upc, quantity)
                    VALUES (:receipt_number, :upc, :quantity)
                """), {
                    'receipt_number': receipt_number,
                    'upc': upc,
                    'quantity': quantity
                })

                # Оновлюємо кількість товару або видаляємо, якщо залишок 0
                new_quantity = stock - quantity

                if new_quantity > 0:
                    db.session.execute(text("""
                            UPDATE store_product SET quantity = :qty WHERE upc = :upc
                        """), {'qty': new_quantity, 'upc': upc})
                else:
                    db.session.execute(text("""
                            DELETE FROM store_product WHERE upc = :upc
                        """), {'upc': upc})

            db.session.commit()
            return jsonify({'success': True, 'receipt_number': receipt_number})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400

    return render_template("add_receipt.html", user=current_user, receipt_number=generate_receipt_number())
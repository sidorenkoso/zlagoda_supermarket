from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, jsonify
from flask_login import login_required, current_user
from zlg_website import db
from . import views
from datetime import datetime
from sqlalchemy import text


@views.route('/categories/report')
@login_required
def print_categories_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Використовуємо чистий SQL запит для отримання всіх категорій
    sql_query = text("""
        SELECT id, name, description 
        FROM Category
        ORDER BY name
    """)

    categories = db.session.execute(sql_query).mappings().all()
    return render_template('print_categories.html', categories=categories, user=current_user)


@views.route('/print_receipts_report')
@login_required
def print_receipts_report():
    """Generate a printable report of receipts based on current filters"""
    if current_user.position != 'Менеджер':
        abort(403)

    # Get the same filters as in the receipts view
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # Базовий SQL запит для отримання чеків
    base_query = """
        SELECT r.receipt_number, r.date, e.first_name, e.last_name
        FROM Receipt r
        JOIN Employee e ON r.employee_id = e.id
    """

    where_conditions = []
    params = {}

    if employee_id:
        where_conditions.append("r.employee_id = :employee_id")
        params['employee_id'] = employee_id

    if date_from:
        where_conditions.append("DATE(r.date) >= DATE(:date_from)")
        params['date_from'] = date_from

    if date_to:
        where_conditions.append("DATE(r.date) <= DATE(:date_to)")
        params['date_to'] = date_to

    if where_conditions:
        base_query += " WHERE " + " AND ".join(where_conditions)

    base_query += " ORDER BY r.date DESC"

    receipts_data = db.session.execute(text(base_query), params).mappings().all()

    # Обробка даних чеків
    receipts = []
    total_sum = 0

    for r in receipts_data:
        items_query = text("""
            SELECT ri.upc, ri.quantity, 
                   CASE 
                       WHEN sp.is_promotional = TRUE THEN sp.promo_price 
                       ELSE sp.price 
                   END as price
            FROM ReceiptItem ri
            JOIN StoreProduct sp ON ri.upc = sp.upc
            WHERE ri.receipt_number = :receipt_number
        """)

        items = db.session.execute(items_query, {'receipt_number': r['receipt_number']}).mappings().all()

        receipt_total = sum(item['price'] * item['quantity'] for item in items)
        vat = receipt_total * 0.2

        total_sum += receipt_total

        receipt = {
            'receipt_number': r['receipt_number'],
            'date': r['date'],
            'total_sum': receipt_total,
            'vat': vat,
            'employee': {
                'first_name': r['first_name'],
                'last_name': r['last_name']
            }
        }

        receipts.append(receipt)

    return render_template(
        'print_receipts_report.html',
        receipts=receipts,
        total_sum=total_sum,
        date_from=date_from,
        date_to=date_to,
        generated_at=datetime.now().strftime('%d.%m.%Y %H:%M')
    )


@views.route('/employees/report')
@login_required
def print_employees_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Використовуємо чистий SQL запит для отримання всіх робітників
    sql_query = text("""
        SELECT id, first_name, last_name, position, salary, birth_date, 
               start_date, phone, address
        FROM Employee
        ORDER BY last_name, first_name
    """)



    employees = db.session.execute(sql_query).mappings().all()
    return render_template('print_employees.html', employees=employees, user=current_user)


@views.route('/products/report')
@login_required
def print_products_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Використовуємо чистий SQL запит для отримання всіх продуктів з інформацією про категорії
    sql_query = text("""
        SELECT p.id, p.name, p.characteristics, c.name as category_name
        FROM Product p
        LEFT JOIN Category c ON p.category_id = c.id
        ORDER BY p.name
    """)

    products = db.session.execute(sql_query).mappings().all()
    return render_template('print_products.html', products=products, user=current_user)


@views.route('/storeproducts/report')
@login_required
def print_storeproducts_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Використовуємо чистий SQL запит для отримання всіх товарів у магазині
    sql_query = text("""
        SELECT sp.upc, p.name, sp.price, sp.quantity, sp.is_promotional, 
               sp.promo_price, sp.promotional_start_date, sp.promotional_end_date
        FROM StoreProduct sp
        JOIN Product p ON sp.product_id = p.id
        ORDER BY p.name
    """)

    products = db.session.execute(sql_query).mappings().all()
    return render_template('print_storeproducts.html', products=products, user=current_user)


@views.route('/clients/report')
@login_required
def print_clients_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Використовуємо чистий SQL запит для отримання всіх клієнтів
    sql_query = text("""
        SELECT card_number, cust_surname, cust_name, cust_patronymic, 
               phone_number, city, street, zip_code, percent
        FROM CustomerCard
        ORDER BY cust_surname, cust_name
    """)

    clients = db.session.execute(sql_query).mappings().all()
    date = datetime.now().strftime('%d.%m.%Y')
    return render_template('print_clients.html', clients=clients, date=date, user=current_user)
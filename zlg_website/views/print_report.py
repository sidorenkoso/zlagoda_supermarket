from flask import Blueprint, render_template, redirect, url_for, request, abort, flash, jsonify
from flask_login import login_required, current_user
from zlg_website import db
from . import views
from datetime import datetime
from sqlalchemy import text
from ..models import Employee, StoreProduct, CustomerCard
from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import text
from . import views
from .. import db


@views.route('/categories/report')
@login_required
def print_categories_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Використовуємо чистий SQL запит для отримання всіх категорій
    sql_query = text("""
        SELECT category_number, name 
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

    # Отримуємо фільтри, якщо вони є
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

    # Виконуємо чистий SQL запит для отримання чеків і отримуємо результат як мапінг
    receipts_data = db.session.execute(text(base_query), params).mappings().all()

    receipts = []
    total_sum = 0

    for row in receipts_data:
        receipt_number = row['receipt_number']
        receipt_date = row['date']
        employee_first_name = row['first_name']
        employee_last_name = row['last_name']

        # Отримуємо деталі чека
        items_query = """
            SELECT ri.upc, ri.quantity, 
                   CASE 
                       WHEN sp.is_promotional = TRUE THEN sp.promo_price 
                       ELSE sp.price 
                   END as price
            FROM ReceiptItem ri
            JOIN StoreProduct sp ON ri.upc = sp.upc
            WHERE ri.receipt_number = :receipt_number
        """

        items = db.session.execute(text(items_query), {'receipt_number': receipt_number}).mappings().all()

        receipt_total = sum(item['price'] * item['quantity'] for item in items)
        vat = receipt_total * 0.2

        total_sum += receipt_total

        receipt = {
            'receipt_number': receipt_number,
            'date': receipt_date,
            'total_sum': receipt_total,
            'vat': vat,
            'employee': {
                'first_name': employee_first_name,
                'last_name': employee_last_name
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

    # Оновлений SQL-запит для отримання всіх необхідних полів
    sql_query = text("""
        SELECT id, first_name, last_name, middle_name, position, salary, birth_date, 
               start_date, phone, city, street, postal_code, email
        FROM Employee
        ORDER BY last_name, first_name
    """)

    # Виконання запиту
    result = db.session.execute(sql_query).mappings().all()

    # Формуємо список працівників із додатковими полями full_name та address
    employees = []
    for row in result:
        employee = dict(row)  # Перетворюємо RowMapping в звичайний словник
        # Формуємо full_name
        employee['full_name'] = f"{employee['first_name']} {employee['middle_name']} {employee['last_name']}"

        # Формуємо address
        employee['address'] = f"{employee['city']}, {employee['street']}, {employee['postal_code']}"

        employees.append(employee)

    current_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    # Передаємо сформовані дані в шаблон
    return render_template('print_employees.html', employees=employees, user=current_user, now=current_time)


@views.route('/products/report')
@login_required
def print_products_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Використовуємо чистий SQL запит для отримання всіх продуктів з інформацією про категорії
    sql_query = text("""
        SELECT p.id, p.name, p.manufacturer, p.specifications
        FROM Product p
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
        SELECT sp.upc, p.name AS product_name, sp.price, sp.quantity, sp.is_promotional, 
               sp.promo_price, c.name AS category_name
        FROM StoreProduct sp
        JOIN Product p ON sp.product_id = p.id
        JOIN Category c ON p.category_number = c.category_number
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
        SELECT c.card_number, c.last_name, c.first_name, c.middle_name, 
               c.phone, c.city, c.street, c.postal_code, c.discount_percent
        FROM CustomerCard c
        ORDER BY last_name, first_name
    """)

    clients = db.session.execute(sql_query).mappings().all()
    date = datetime.now().strftime('%d.%m.%Y')
    return render_template('print_clients.html', clients=clients, date=date, user=current_user)

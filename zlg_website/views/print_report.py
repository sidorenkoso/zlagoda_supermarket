from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Category, db, Receipt, Employee, Product, StoreProduct, CustomerCard
from . import views

@views.route('/categories/report')
@login_required
def print_categories_report():
    if current_user.position != 'Менеджер':
        abort(403)

    categories = Category.query.all()
    return render_template('print_categories.html', categories=categories, user=current_user)

@views.route('/receipts/report')
@login_required
def print_receipts_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Отримуємо всі чеки для звіту
    receipts = Receipt.query.all()
    return render_template('print_receipts.html', receipts=receipts, user=current_user)

@views.route('/employees/report')
@login_required
def print_employees_report():
    if current_user.position != 'Менеджер':
        abort(403)

    # Отримуємо всіх робітників для звіту
    employees = Employee.query.all()
    return render_template('print_employees.html', employees=employees, user=current_user)

@views.route('/products/report')
@login_required
def print_products_report():
    if current_user.position != 'Менеджер':
        abort(403)

    products = Product.query.all()
    return render_template('print_products.html', products=products, user=current_user)

@views.route('/storeproducts/report')
@login_required
def print_storeproducts_report():
    if current_user.position != 'Менеджер':
        abort(403)

    products = StoreProduct.query.all()
    return render_template('print_storeproducts.html', products=products, user=current_user)

@views.route('/clients/report')
@login_required
def print_clients_report():
    if current_user.position != 'Менеджер':
        abort(403)

    clients = CustomerCard.query.all()
    date = datetime.now().strftime('%d.%m.%Y')
    return render_template('print_clients.html', clients=clients, date=date, user=current_user)
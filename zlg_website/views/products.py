from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from zlg_website.models import Product  # імпорт моделі Category
from . import views

@views.route('/products')
@login_required
def products():
    search_query = request.args.get('search', '')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    query = Product.query

    # Сортування
    if sort == 'name':
        query = query.order_by(
            Product.name.desc() if order == 'desc' else Product.name.asc()
        )
    elif sort == 'id':
        query = query.order_by(
            Product.id.asc()
        )
    else:
        query = query.order_by(Product.id.asc())  # За замовчуванням — за id

    products = query.all()

    # Пошук за назвою товару
    if search_query:
        search_lower = search_query.lower()
        products = [p for p in products if search_lower in p.name.lower()]

    return render_template("products.html", user=current_user, products=products, search_query=search_query, sort=sort, order=order)


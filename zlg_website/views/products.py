from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from zlg_website.models import Product, Category  # імпорт моделі Category
from . import views

@views.route('/products')
@login_required
def products():
    category_number = request.args.get('category')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')
    search_query = request.args.get('search', '')

    query = Product.query

    if category_number:
        try:
            category_number = int(category_number)  # Перетворення на int
            query = query.filter(Product.category_number == category_number)
        except ValueError:
            pass

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

    if search_query:
        search_lower = search_query.lower()
        products = [
            product for product in products
            if search_lower in product.name.lower()
        ]

    categories = Category.query.all()

    return render_template("products.html", user=current_user, products=products, categories=categories, sort=sort, order=order, category_number=category_number,
        search_query=search_query)


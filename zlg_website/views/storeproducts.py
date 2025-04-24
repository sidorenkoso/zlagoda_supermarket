from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from zlg_website.models import StoreProduct, Product, Category  # імпорт моделі Category
from . import views

@views.route('/stock')
@login_required
def storeproducts():
    category_number = request.args.get('category')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    query = StoreProduct.query.join(Product)

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
    categories = Category.query.all()

    return render_template("storeproducts.html", user=current_user, products=products, categories=categories, sort=sort, order=order, category_number=category_number)


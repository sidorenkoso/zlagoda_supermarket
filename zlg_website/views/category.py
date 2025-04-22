from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from zlg_website.models import Category  # імпорт моделі Category
from . import views

@views.route('/categories')
@login_required
def categories():
    if current_user.position != 'Менеджер':
        abort(403)

    search_query = request.args.get('search', '')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    query = Category.query

    # Сортування
    if sort == 'name':
        query = query.order_by(
            Category.name.desc() if order == 'desc' else Category.name.asc()
        )
    elif sort == 'number':
        query = query.order_by(
            Category.category_number.asc()
        )
    else:
        query = query.order_by(Category.category_number.asc())

    categories = query.all()

    # Пошук (за частковим збігом назви)
    if search_query:
        search_lower = search_query.lower()
        categories = [c for c in categories if search_lower in c.name.lower()]

    return render_template("category.html", user=current_user, categories=categories,
                           search_query=search_query, sort=sort, order=order)

@views.route('/categories/<int:category_id>')
@login_required
def view_category(category_id):
    category = Category.query.get_or_404(category_id)
    return render_template('goods.html', category=category, user=current_user)
    # Пошук (за частковим збігом назви)
    if search_query:
        search_lower = search_query.lower()
        categories = [c for c in categories if search_lower in c.name.lower()]

    return render_template("category.html", user=current_user, categories=categories,
                           search_query=search_query, sort=sort, order=order)

@views.route('/categories/<int:category_id>')
@login_required
def view_category(category_id):
    category = Category.query.get_or_404(category_id)
    return render_template('products_in_category.html', category=category, user=current_user)

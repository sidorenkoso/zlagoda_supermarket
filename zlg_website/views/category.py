from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from flask_login import login_required, current_user
from zlg_website.models import Category, Product  # імпорт моделі Category
from . import views
from .. import db


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
    if not category:
        flash('Категорія не знайдена', 'danger')
        return redirect(url_for('views.categories'))

    products = Product.query.filter_by(category_number=category_id).all()
    return render_template('products_in_category.html', category=category, products=products, user=current_user)



@views.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash("Назва не може бути порожньою", 'error')
        else:
            category.name = name
            db.session.commit()
            flash("Категорію оновлено", 'success')
            return redirect(url_for('views.categories'))
    return render_template('form_category.html', category=category, user=current_user)

@views.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if current_user.position != 'Менеджер':
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name')

        if not name:
            flash("Назва категорії не може бути порожньою.", category="error")
        else:
            new_category = Category(name=name)
            db.session.add(new_category)
            try:
                db.session.commit()
                flash("Категорію успішно додано!", category="success")
                return redirect(url_for('views.categories'))
            except Exception as e:
                db.session.rollback()
                flash(f"Помилка при додаванні категорії: {str(e)}", "error")
                return redirect(url_for("views.add_category"))

    # Обчислюємо next_id тільки якщо GET-запит
    last_category = Category.query.order_by(Category.category_number.desc()).first()
    next_id = (last_category.category_number + 1) if last_category else 1

    return render_template("form_category.html", user=current_user, next_id=next_id)

@views.route('/categories/<int:category_id>/delete')
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.products:
        flash("Неможливо видалити категорію, оскільки в ній є товари.", 'error')
        return redirect(url_for('views.categories'))

    db.session.delete(category)
    db.session.commit()
    flash("Категорію видалено", 'success')
    return redirect(url_for('views.categories'))



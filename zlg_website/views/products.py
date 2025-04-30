from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from zlg_website.models import Product, Category  # імпорт моделі Category
from . import views
from .. import db


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


@views.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    if product.store_items:
        flash("Неможливо видалити товар, оскільки він є в наявності.", 'error')
        return redirect(url_for('views.products'))

    db.session.delete(product)
    db.session.commit()
    flash("Товар видалено", 'success')
    return redirect(url_for('views.products'))


@views.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        name = request.form.get('name')
        manufacturer = request.form.get('manufacturer')
        specifications = request.form.get('specifications')
        category_number = request.form.get('category_number')



        if not name or not manufacturer or  not category_number:
            flash("Усі обов'язкові поля мають бути заповнені.", 'error')
        else:
            product.name = name
            product.manufacturer = manufacturer
            product.specifications = specifications
            product.category_number = int(category_number)
            db.session.commit()
            flash("Товар оновлено", 'success')
            return redirect(url_for('views.products'))

    categories = Category.query.all()
    return render_template('form_products.html', product=product, user=current_user, categories=categories)


@views.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.position != 'Менеджер':
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name')
        manufacturer = request.form.get('manufacturer')
        specifications = request.form.get('specifications')
        category_number = request.form.get('category_number')

        if not name or not manufacturer or not category_number:
            flash("Усі обов'язкові поля мають бути заповнені.", "error")
        else:
            new_product = Product(
                name=name,
                manufacturer=manufacturer,
                specifications=specifications,
                category_number=category_number
            )
            db.session.add(new_product)
            try:
                db.session.commit()
                flash("Товар успішно додано!", "success")
                return redirect(url_for('views.products'))
            except Exception as e:
                db.session.rollback()
                flash(f"Помилка при додаванні товару: {str(e)}", "error")
                return redirect(url_for("views.add_product"))

    categories = Category.query.all()
    next_id = (db.session.query(db.func.max(Product.id)).scalar() or 0) + 1
    return render_template("form_products.html", user=current_user, categories=categories, next_id=next_id)
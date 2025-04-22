from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from zlg_website.models import Product, Category, db
from . import views

@views.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        name = request.form.get('name')
        manufacturer = request.form.get('manufacturer')
        specifications = request.form.get('specifications')
        category_number = request.form.get('category_number')

        if not name or not manufacturer or not category_number:
            flash("Усі обов'язкові поля мають бути заповнені.", 'error')
        else:
            product.name = name
            product.manufacturer = manufacturer
            product.specifications = specifications
            product.category_number = category_number
            db.session.commit()
            flash("Товар оновлено", 'success')
            return redirect(url_for('views.products'))

    categories = Category.query.all()
    return render_template('form_products.html', product=product, user=current_user, categories=categories)

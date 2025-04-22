from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from zlg_website.models import Product, Category, db
from . import views

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
    return render_template("form_products.html", user=current_user, categories=categories)

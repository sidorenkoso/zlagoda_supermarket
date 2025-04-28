from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from zlg_website.models import StoreProduct, Product, db
from . import views

@views.route('/storeproducts/add', methods=['GET', 'POST'])
@login_required
def add_storeproduct():
    if current_user.position != 'Менеджер':
        abort(403)

    if request.method == 'POST':
        upc = request.form.get('upc')
        product_id = request.form.get('product_id')
        price = request.form.get('price')
        promo_price = request.form.get('promo_price')
        quantity = request.form.get('quantity')
        expiration_date = request.form.get('expiration_date')
        is_promotional = bool(request.form.get('is_promotional'))

        if not upc or not product_id or not price or not quantity:
            flash("Обов'язкові поля повинні бути заповнені.", "error")
        else:
            expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None
            new_store_product = StoreProduct(
                upc=upc,
                product_id=product_id,
                price=price,
                promo_price=promo_price if promo_price else None,
                quantity=quantity,
                expiration_date=expiration_date if expiration_date else None,
                is_promotional=is_promotional
            )
            db.session.add(new_store_product)
            try:
                db.session.commit()
                flash("Товар у магазині додано успішно!", "success")
                return redirect(url_for('views.storeproducts'))
            except Exception as e:
                db.session.rollback()
                flash(f"Помилка при додаванні товару у магазин: {str(e)}", "error")
                return redirect(url_for("views.add_storeproduct"))

    subquery = db.session.query(StoreProduct.product_id).filter(StoreProduct.product_id != None)
    print("Subquery result:", [item for item in subquery])  # Виводимо ID товарів, які вже є в StoreProduct
    products = Product.query.filter(~Product.id.in_(subquery)).all()
    print("Products:", products)  # Виводимо результати пошуку товарів, яких нема в StoreProduct

    return render_template("form_storeproduct.html", user=current_user, products=products)

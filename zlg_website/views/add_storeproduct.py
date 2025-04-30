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

    storeproduct = None

    if request.method == 'POST':
        upc = request.form.get('upc')
        product_id = request.form.get('product_id')
        price = float(request.form.get('price'))
        promo_price = request.form.get('promo_price')
        quantity = int(request.form.get('quantity'))
        expiration_date = request.form.get('expiration_date')
        is_promotional = 'is_promotional' in request.form

        expiration_date = datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None

        storeproduct = StoreProduct.query.filter_by(upc=upc).first()

        if storeproduct:
            # Оновлення існуючого товару
            storeproduct.price = price
            storeproduct.promo_price = float(promo_price) if promo_price else None
            storeproduct.is_promotional = is_promotional
            storeproduct.quantity += quantity
            storeproduct.expiration_date = expiration_date
            flash("Інформацію про товар оновлено успішно!", "success")
        else:
            if not upc or not product_id or not price or not quantity:
                flash("Обов'язкові поля повинні бути заповнені.", "error")
                return redirect(url_for("views.add_storeproduct"))

            new_store_product = StoreProduct(
                upc=upc,
                product_id=product_id,
                price=price,
                promo_price=float(promo_price) if promo_price else None,
                quantity=quantity,
                expiration_date=expiration_date,
                is_promotional=is_promotional
            )
            db.session.add(new_store_product)
            flash("Товар у магазині додано успішно!", "success")

        try:
            db.session.commit()
            return redirect(url_for('views.storeproducts'))
        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при збереженні товару: {str(e)}", "error")
            return redirect(url_for("views.add_storeproduct"))

    products = Product.query.all()
    return render_template("form_storeproduct.html", user=current_user, products=products, storeproduct=storeproduct)


from flask import jsonify

@views.route('/storeproducts/fetch/<int:product_id>')
@login_required
def fetch_storeproduct(product_id):
    if current_user.position != 'Менеджер':
        abort(403)

    storeproduct = StoreProduct.query.filter_by(product_id=product_id).first()

    if storeproduct:
        return jsonify({
            "exists": True,
            "upc": storeproduct.upc,
            "price": float(storeproduct.price),
            "expiration_date": storeproduct.expiration_date.isoformat() if storeproduct.expiration_date else ""
        })
    else:
        # Якщо товару ще немає в наявності — згенеруємо UPC
        last_storeproduct = StoreProduct.query.order_by(StoreProduct.upc.desc()).first()
        try:
            new_upc = str(int(last_storeproduct.upc) + 1) if last_storeproduct else "100000000000"
        except ValueError:
            new_upc = "100000000000"

        return jsonify({
            "exists": False,
            "upc": new_upc
        })


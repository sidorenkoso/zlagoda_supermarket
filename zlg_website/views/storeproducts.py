from flask import jsonify
from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from zlg_website.models import StoreProduct, Product, Category
from . import views
from .. import db
from datetime import datetime


@views.route('/stock')
@login_required
def storeproducts():
    category_number = request.args.get('category')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')
    promo_filter = request.args.get('promo')
    search = request.args.get('search')
    quantity_filter = request.args.get('quantity')

    query = StoreProduct.query.join(Product)

    if category_number:
        try:
            category_number = int(category_number)  # Перетворення на int
            query = query.filter(Product.category_number == category_number)
        except ValueError:
            pass

    if promo_filter == 'yes':
        query = query.filter(StoreProduct.is_promotional.is_(True))
    elif promo_filter == 'no':
        query = query.filter(StoreProduct.is_promotional.is_(False))

    if quantity_filter:
        try:
            quantity_filter = int(quantity_filter)
            query = query.filter(StoreProduct.quantity >= quantity_filter)  # Товари з кількістю більше або рівною
        except ValueError:
            pass

    # Сортування
    if sort == 'name':
        query = query.order_by(
            Product.name.desc() if order == 'desc' else Product.name.asc()
        )
    elif sort == 'quantity':
        query = query.order_by(
            StoreProduct.quantity.desc() if order == 'desc' else StoreProduct.quantity.asc()
        )
    elif sort == 'id':
        query = query.order_by(Product.id.asc())
    else:
        query = query.order_by(Product.id.asc())  # За замовчуванням — за id

    if search:
        query = query.filter(StoreProduct.upc.ilike(f"{search}%"))

    products = query.all()
    categories = Category.query.all()

    return render_template("storeproducts.html", user=current_user, products=products, categories=categories, sort=sort, order=order, category_number=category_number, current_promo_filter=promo_filter, quantity_filter=quantity_filter)




@views.route('/storeproducts/edit/<string:upc>', methods=['GET', 'POST'])
@login_required
def edit_storeproduct(upc):
    storeproduct = StoreProduct.query.get_or_404(upc)

    if request.method == 'POST':
        try:
            is_promotional = 'is_promotional' in request.form
            new_price = float(request.form.get('price'))
            new_quantity = int(request.form.get('quantity'))
            expiration_date_str = request.form.get('expiration_date')

            # Оновлення основної ціни та кількості
            storeproduct.price = new_price
            storeproduct.quantity = new_quantity
            storeproduct.expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date() if expiration_date_str else None

            if is_promotional:
                storeproduct.is_promotional = True
                storeproduct.promo_price = round(new_price * 0.8, 2)
            else:
                storeproduct.is_promotional = False
                storeproduct.promo_price = None

            db.session.commit()
            flash("Товар у наявності успішно оновлено", "success")
            return redirect(url_for('views.storeproducts'))

        except ValueError as ve:
            db.session.rollback()
            flash(f"Невірний формат даних: {str(ve)}", "error")
        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при оновленні: {str(e)}", "error")

    products = Product.query.all()
    return render_template('edit_storeproduct.html',
                           storeproduct=storeproduct,
                           products=products,
                           user=current_user)


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
            storeproduct.quantity += quantity
            storeproduct.expiration_date = expiration_date
            if is_promotional:
                storeproduct.promo_price = round(price * 0.8, 2)
            else:
                storeproduct.promo_price = None

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
    return render_template("add_storeproduct.html", user=current_user, products=products, storeproduct=storeproduct)


@views.route('/storeproducts/<string:upc>/delete', methods=['POST'])
@login_required
def delete_storeproduct(upc):
    store_product = StoreProduct.query.get_or_404(upc)

    db.session.delete(store_product)
    db.session.commit()
    flash("Товар у магазині успішно видалено", 'success')
    return redirect(url_for('views.storeproducts'))


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
            "expiration_date": storeproduct.expiration_date.isoformat() if storeproduct.expiration_date else "",
            "is_promotional": storeproduct.is_promotional
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

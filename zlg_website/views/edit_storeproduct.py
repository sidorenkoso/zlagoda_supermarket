from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from datetime import datetime
from zlg_website.models import StoreProduct, Product, db
from . import views

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

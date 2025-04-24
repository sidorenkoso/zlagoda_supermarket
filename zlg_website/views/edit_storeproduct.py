from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from zlg_website.models import StoreProduct, Product, db
from . import views

@views.route('/storeproducts/edit/<string:upc>', methods=['GET', 'POST'])
@login_required
def edit_storeproduct(upc):
    storeproduct = StoreProduct.query.get_or_404(upc)

    if request.method == 'POST':
        try:
            storeproduct.price = float(request.form.get('price'))
            storeproduct.quantity = int(request.form.get('quantity'))
            storeproduct.expiration_date = request.form.get('expiration_date') or None

            db.session.commit()
            flash("Товар у наявності успішно оновлено", "success")
            return redirect(url_for('views.storeproducts'))
        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при оновленні товару: {str(e)}", "error")

    products = Product.query.all()
    return render_template('form_storeproduct.html',
                           storeproduct=storeproduct,
                           products=products,
                           user=current_user)

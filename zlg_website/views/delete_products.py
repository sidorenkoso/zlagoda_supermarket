from flask import redirect, url_for, flash
from flask_login import login_required, current_user
from zlg_website.models import Product, db
from . import views

@views.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    db.session.delete(product)
    db.session.commit()
    flash("Товар видалено", 'success')
    return redirect(url_for('views.products'))

from flask import redirect, url_for, flash
from flask_login import login_required
from zlg_website.models import StoreProduct, db
from . import views

@views.route('/storeproducts/<string:upc>/delete', methods=['POST'])
@login_required
def delete_storeproduct(upc):
    store_product = StoreProduct.query.get_or_404(upc)

    db.session.delete(store_product)
    db.session.commit()
    flash("Товар у магазині успішно видалено", 'success')
    return redirect(url_for('views.storeproducts'))

from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Category, db
from . import views

@views.route('/categories/<int:category_id>/delete')
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)

    if category.products:
        flash("Неможливо видалити категорію, оскільки в ній є товари.", 'error')
        return redirect(url_for('views.categories'))

    db.session.delete(category)
    db.session.commit()
    flash("Категорію видалено", 'success')
    return redirect(url_for('views.categories'))
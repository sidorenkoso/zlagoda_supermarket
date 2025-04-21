from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Category, db
from . import views

@views.route('/categories/<int:category_id>/delete')
@login_required
def delete_category(category_id):
    #прописати вихід, якщо в категорії є товари

    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Категорію видалено", 'success')
    return redirect(url_for('views.categories'))
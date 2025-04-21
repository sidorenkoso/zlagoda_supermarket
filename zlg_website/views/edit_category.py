from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Category, db
from . import views

@views.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash("Назва не може бути порожньою", 'error')
        else:
            category.name = name
            db.session.commit()
            flash("Категорію оновлено", 'success')
            return redirect(url_for('views.categories'))
    return render_template('edit_category.html', category=category, user=current_user)
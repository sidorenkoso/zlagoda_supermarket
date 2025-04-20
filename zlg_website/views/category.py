from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from zlg_website.models import Category  # імпорт моделі Category
from . import views

@views.route('/categories')
@login_required
def categories():
    if current_user.position != 'Менеджер':
        abort(403)



    query = Category.query
    categories = query.all()

    return render_template("category.html", user=current_user, categories=categories)

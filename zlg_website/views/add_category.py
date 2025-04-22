from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from zlg_website.models import Category, db
from . import views

@views.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if current_user.position != 'Менеджер':
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name')

        if not name:
            flash("Назва категорії не може бути порожньою.", category="error")
        else:
            new_category = Category(name=name)
            db.session.add(new_category)
            try:
                db.session.commit()
                flash("Категорію успішно додано!", category="success")
                return redirect(url_for('views.categories'))
            except Exception as e:
                db.session.rollback()
                flash(f"Помилка при додаванні категорії: {str(e)}", "error")
                return redirect(url_for("views.add_category"))

    # Обчислюємо next_id тільки якщо GET-запит
    last_category = Category.query.order_by(Category.category_number.desc()).first()
    next_id = (last_category.category_number + 1) if last_category else 1

    return render_template("add_category.html", user=current_user, next_id=next_id)

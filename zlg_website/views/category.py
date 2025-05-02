from flask import Blueprint, render_template, request, abort, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import text
from . import views
from .. import db


@views.route('/categories')
@login_required
def categories():
   if current_user.position != 'Менеджер':
       abort(403)


   search_query = request.args.get('search', '')
   sort = request.args.get('sort')
   order = request.args.get('order', 'asc')


   base_query = "SELECT * FROM Category"


   if sort == 'name':
       base_query += " ORDER BY name {}".format('DESC' if order == 'desc' else 'ASC')
   elif sort == 'number':
       base_query += " ORDER BY category_number ASC"
   else:
       base_query += " ORDER BY category_number ASC"


   result = db.session.execute(text(base_query))
   categories = [dict(row._mapping) for row in result.fetchall()]


   if search_query:
       search_lower = search_query.lower()
       categories = [c for c in categories if search_lower in c['name'].lower()]


   return render_template("category.html", user=current_user, categories=categories,
                          search_query=search_query, sort=sort, order=order)




@views.route('/categories/<int:category_id>')
@login_required
def view_category(category_id):
   category_result = db.session.execute(text("SELECT * FROM Category WHERE category_number = :id"), {'id': category_id})
   category_row = category_result.fetchone()
   if not category_row:
       flash('Категорія не знайдена', 'danger')
       return redirect(url_for('views.categories'))


   category = dict(category_row._mapping)


   products_result = db.session.execute(text("SELECT * FROM Product WHERE category_number = :id"), {'id': category_id})
   products = [dict(row._mapping) for row in products_result.fetchall()]


   return render_template('products_in_category.html', category=category, products=products, user=current_user)




@views.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
   if request.method == 'POST':
       name = request.form.get('name')
       if not name:
           flash("Назва не може бути порожньою", 'error')
       else:
           db.session.execute(
               text("UPDATE Category SET name = :name WHERE category_number = :id"),
               {'name': name, 'id': category_id}
           )
           db.session.commit()
           flash("Категорію оновлено", 'success')
           return redirect(url_for('views.categories'))


   result = db.session.execute(text("SELECT * FROM Category WHERE category_number = :id"), {'id': category_id})
   category_row = result.fetchone()
   if not category_row:
       abort(404)
   category = dict(category_row._mapping)
   return render_template('form_category.html', category=category, user=current_user)




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
           try:
               db.session.execute(text("INSERT INTO Category (name) VALUES (:name)"), {'name': name})
               db.session.commit()
               flash("Категорію успішно додано!", category="success")
               return redirect(url_for('views.categories'))
           except Exception as e:
               db.session.rollback()
               flash(f"Помилка при додаванні категорії: {str(e)}", "error")
               return redirect(url_for("views.add_category"))


   result = db.session.execute(text("SELECT * FROM Category ORDER BY category_number DESC LIMIT 1"))
   last_category = result.fetchone()
   next_id = (last_category._mapping['category_number'] + 1) if last_category else 1


   return render_template("form_category.html", user=current_user, next_id=next_id)




@views.route('/categories/<int:category_id>/delete')
@login_required
def delete_category(category_id):
   product_check = db.session.execute(
       text("SELECT 1 FROM Product WHERE category_number = :id LIMIT 1"),
       {'id': category_id}
   ).fetchone()


   if product_check:
       flash("Неможливо видалити категорію, оскільки в ній є товари.", 'error')
       return redirect(url_for('views.categories'))


   db.session.execute(text("DELETE FROM Category WHERE category_number = :id"), {'id': category_id})
   db.session.commit()
   flash("Категорію видалено", 'success')
   return redirect(url_for('views.categories'))
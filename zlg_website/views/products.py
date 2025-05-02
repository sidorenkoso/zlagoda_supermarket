from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import text
from sqlalchemy.orm import joinedload


from . import views
from .. import db
from ..models import Product, Employee


@views.route('/products')
@login_required
def products():
   category_number = request.args.get('category')
   sort = request.args.get('sort')
   order = request.args.get('order', 'asc')
   search_query = request.args.get('search', '')


   # Будуємо базовий SQL запит
   sql_str = """
       SELECT p.*, c.name AS category_name
       FROM product p
       JOIN category c ON p.category_number = c.category_number
   """
   where_clauses = []
   params = {}


   # Додаємо умови WHERE
   if category_number:
       where_clauses.append("p.category_number = :category_number")
       params['category_number'] = int(category_number)


   # Додаємо пошук за назвою через SQL, а не Python
   if search_query:
       where_clauses.append("LOWER(p.name) LIKE :search_query")
       params['search_query'] = f"%{search_query.lower()}%"


   # Об'єднуємо умови WHERE, якщо вони є
   if where_clauses:
       sql_str += " WHERE " + " AND ".join(where_clauses)


   # Додаємо ORDER BY
   if sort == 'name':
       sql_str += f" ORDER BY p.name {order}"
   elif sort == 'id':
       sql_str += f" ORDER BY p.id {order}"
   else:
       sql_str += " ORDER BY p.id ASC"  # Значення за замовчуванням


   # Виконуємо запит
   stmt = text(sql_str)
   result = db.session.execute(stmt, params)


   # Перетворюємо результат у список словників для шаблону
   products = [dict(row._mapping) for row in result.fetchall()]


   # Отримуємо всі категорії для фільтра
   categories_sql = text("SELECT * FROM category")
   categories_result = db.session.execute(categories_sql)
   categories = [dict(row._mapping) for row in categories_result.fetchall()]


   return render_template(
       "products.html",
       user=current_user,
       products=products,
       categories=categories,
       sort=sort,
       order=order,
       category_number=category_number,
       search_query=search_query
   )






@views.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
   # Перевірка на наявність товару
   sql = text("""
       SELECT * FROM store_product
       WHERE product_id = :product_id
   """)
   result = db.session.execute(sql, {'product_id': product_id})
   store_product = result.fetchone()


   if store_product:
       flash("Неможливо видалити товар, оскільки він є в наявності.", 'error')
       return redirect(url_for('views.products'))


   # Видалення товару
   delete_sql = text("""
       DELETE FROM product WHERE id = :product_id
   """)
   db.session.execute(delete_sql, {'product_id': product_id})
   db.session.commit()
   flash("Товар видалено", 'success')
   return redirect(url_for('views.products'))




@views.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
   # Отримання даних про товар
   sql = text("""
       SELECT * FROM product WHERE id = :product_id
   """)
   result = db.session.execute(sql, {'product_id': product_id})
   product = result.fetchone()


   if not product:
       flash("Товар не знайдений", 'error')
       return redirect(url_for('views.products'))


   if request.method == 'POST':
       name = request.form.get('name')
       manufacturer = request.form.get('manufacturer')
       specifications = request.form.get('specifications')
       category_number = request.form.get('category_number')


       if not name or not manufacturer or not category_number:
           flash("Усі обов'язкові поля мають бути заповнені.", 'error')
       else:
           update_sql = text("""
               UPDATE product
               SET name = :name, manufacturer = :manufacturer, specifications = :specifications, category_number = :category_number
               WHERE id = :product_id
           """)
           db.session.execute(update_sql,
                              {'name': name, 'manufacturer': manufacturer, 'specifications': specifications,
                               'category_number': category_number, 'product_id': product_id})
           db.session.commit()
           flash("Товар оновлено", 'success')
           return redirect(url_for('views.products'))


   # Отримуємо категорії для вибору
   categories_sql = text("SELECT * FROM category")
   categories_result = db.session.execute(categories_sql)
   categories = [dict(row._mapping) for row in categories_result.fetchall()]


   return render_template('form_products.html', product=product, user=current_user, categories=categories)




@views.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
   if current_user.position != 'Менеджер':
       abort(403)


   if request.method == 'POST':
       name = request.form.get('name')
       manufacturer = request.form.get('manufacturer')
       specifications = request.form.get('specifications')
       category_number = request.form.get('category_number')


       if not name or not manufacturer or not category_number:
           flash("Усі обов'язкові поля мають бути заповнені.", "error")
       else:
           insert_sql = text("""
               INSERT INTO product (name, manufacturer, specifications, category_number)
               VALUES (:name, :manufacturer, :specifications, :category_number)
           """)
           db.session.execute(insert_sql,
                              {'name': name, 'manufacturer': manufacturer, 'specifications': specifications,
                               'category_number': category_number})
           db.session.commit()
           flash("Товар успішно додано!", "success")
           return redirect(url_for('views.products'))


   # Отримуємо категорії для вибору
   categories_sql = text("SELECT * FROM category")
   categories_result = db.session.execute(categories_sql)
   categories = [dict(row._mapping) for row in categories_result.fetchall()]


   # Генерація наступного ID для товару
   next_id_sql = text("SELECT MAX(id) FROM product")
   next_id_result = db.session.execute(next_id_sql)
   next_id = (next_id_result.scalar() or 0) + 1


   return render_template("form_products.html", user=current_user, categories=categories, next_id=next_id)


@views.route('/product-analytics', methods=['GET'])
@login_required
def product_analytics():
    product_name = request.args.get('product', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    product_found = None
    sales_quantity = 0

    if product_name:
        product_found, sales_quantity = get_product_sales_quantity(product_name, date_from, date_to)

    # Get employee count for the dashboard
    employee_count = len(Employee.get_all())

    return render_template('main.html',
                           user=current_user,
                           employee_count=employee_count,
                           product_name=product_found,
                           sales_quantity=sales_quantity)



def get_product_sales_quantity(product_name, date_from=None, date_to=None):
    query = """
        SELECT p.name AS product_name, SUM(ri.quantity) AS total_quantity
        FROM receipt_item ri
        JOIN store_product sp ON ri.upc = sp.upc
        JOIN product p ON sp.product_id = p.id
        JOIN receipt r ON ri.receipt_number = r.receipt_number
        WHERE p.name LIKE :product_name
    """

    # Add date filters if provided
    params = {"product_name": f"%{product_name}%"}

    if date_from:
        query += " AND r.date >= :date_from"
        params["date_from"] = date_from

    if date_to:
        query += " AND r.date <= :date_to"
        params["date_to"] = date_to

    query += " GROUP BY p.name"

    try:
        result = db.session.execute(text(query), params).fetchone()
        if result:
            return result.product_name, int(result.total_quantity)
        return None, 0
    except Exception as e:
        print(f"Error querying product sales: {e}")
        return None, 0
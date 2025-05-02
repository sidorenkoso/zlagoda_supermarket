from flask import jsonify
from flask import Blueprint, render_template, request, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import text
from . import views
from .. import db
from datetime import datetime




@views.route('/stock')
@login_required
def storeproducts():
   category_number = request.args.get('category')
   sort = request.args.get('sort')
   order = request.args.get('order', 'asc')
   promo_filter = request.args.get('promo')
   search = request.args.get('search')
   quantity_filter = request.args.get('quantity')


   # Базовий SQL-запит для з'єднання store_product з product
   sql_str = """
       SELECT sp.*, p.name, p.manufacturer, p.specifications, p.category_number, c.name as category_name
       FROM store_product sp
       JOIN product p ON sp.product_id = p.id
       JOIN category c ON p.category_number = c.category_number
   """
   where_clauses = []
   params = {}


   # Додаємо умови WHERE
   if category_number:
       try:
           category_number = int(category_number)
           where_clauses.append("p.category_number = :category_number")
           params['category_number'] = category_number
       except ValueError:
           pass


   if promo_filter == 'yes':
       where_clauses.append("sp.is_promotional = TRUE")
   elif promo_filter == 'no':
       where_clauses.append("sp.is_promotional = FALSE")


   if quantity_filter:
       try:
           quantity_filter = int(quantity_filter)
           where_clauses.append("sp.quantity >= :quantity_filter")
           params['quantity_filter'] = quantity_filter
       except ValueError:
           pass


   if search:
       where_clauses.append("sp.upc LIKE :search")
       params['search'] = f"{search}%"


   # Об'єднуємо умови WHERE, якщо вони є
   if where_clauses:
       sql_str += " WHERE " + " AND ".join(where_clauses)


   # Додаємо ORDER BY
   if sort == 'name':
       sql_str += f" ORDER BY p.name {order}"
   elif sort == 'quantity':
       sql_str += f" ORDER BY sp.quantity {order}"
   elif sort == 'id':
       sql_str += " ORDER BY p.id ASC"
   else:
       sql_str += " ORDER BY p.id ASC"  # За замовчуванням — за id


   # Виконуємо запит
   stmt = text(sql_str)
   result = db.session.execute(stmt, params)
   products = [dict(row._mapping) for row in result.fetchall()]


   # Отримуємо всі категорії
   categories_sql = text("SELECT * FROM category")
   categories_result = db.session.execute(categories_sql)
   categories = [dict(row._mapping) for row in categories_result.fetchall()]


   return render_template("storeproducts.html",
                          user=current_user,
                          products=products,
                          categories=categories,
                          sort=sort,
                          order=order,
                          category_number=category_number,
                          current_promo_filter=promo_filter,
                          quantity_filter=quantity_filter)




@views.route('/storeproducts/edit/<string:upc>', methods=['GET', 'POST'])
@login_required
def edit_storeproduct(upc):
   # Отримуємо дані про товар у наявності
   query = text("""
       SELECT sp.*, p.name as product_name
       FROM store_product sp
       JOIN product p ON sp.product_id = p.id
       WHERE sp.upc = :upc
   """)
   result = db.session.execute(query, {"upc": upc})
   storeproduct = result.fetchone()


   if not storeproduct:
       abort(404)


   if request.method == 'POST':
       try:
           is_promotional = 'is_promotional' in request.form
           new_price = float(request.form.get('price'))
           new_quantity = int(request.form.get('quantity'))
           expiration_date_str = request.form.get('expiration_date')


           # Підготовка дати закінчення терміну дії
           expiration_date = None
           if expiration_date_str:
               expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
               expiration_date = expiration_date.strftime('%Y-%m-%d')  # Форматування для SQL


           # Обчислення промо-ціни, якщо товар акційний
           promo_price_value = None
           if is_promotional:
               promo_price_value = round(new_price * 0.8, 2)


           # Оновлення даних про товар
           update_query = text("""
               UPDATE store_product
               SET price = :price, quantity = :quantity,
                   expiration_date = :expiration_date,
                   is_promotional = :is_promotional,
                   promo_price = :promo_price
               WHERE upc = :upc
           """)


           db.session.execute(update_query, {
               "price": new_price,
               "quantity": new_quantity,
               "expiration_date": expiration_date,
               "is_promotional": is_promotional,
               "promo_price": promo_price_value,
               "upc": upc
           })


           db.session.commit()
           flash("Товар у наявності успішно оновлено", "success")
           return redirect(url_for('views.storeproducts'))


       except ValueError as ve:
           db.session.rollback()
           flash(f"Невірний формат даних: {str(ve)}", "error")
       except Exception as e:
           db.session.rollback()
           flash(f"Помилка при оновленні: {str(e)}", "error")


   # Отримання всіх продуктів для форми
   products_query = text("SELECT * FROM product")
   products_result = db.session.execute(products_query)
   products = [dict(row._mapping) for row in products_result.fetchall()]


   return render_template('edit_storeproduct.html',
                          storeproduct=storeproduct,
                          products=products,
                          user=current_user)




@views.route('/storeproducts/add', methods=['GET', 'POST'])
@login_required
def add_storeproduct():
   if current_user.position != 'Менеджер':
       abort(403)


   storeproduct = None


   if request.method == 'POST':
       upc = request.form.get('upc')
       product_id = request.form.get('product_id')
       price = float(request.form.get('price'))
       quantity = int(request.form.get('quantity'))
       expiration_date_str = request.form.get('expiration_date')
       is_promotional = 'is_promotional' in request.form


       # Підготовка дати закінчення терміну дії
       expiration_date = None
       if expiration_date_str:
           expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
           expiration_date = expiration_date.strftime('%Y-%m-%d')  # Форматування для SQL


       # Обчислення промо-ціни, якщо товар акційний
       promo_price = None
       if is_promotional:
           promo_price = round(price * 0.8, 2)


       # Перевіряємо, чи існує вже такий товар
       check_query = text("SELECT * FROM store_product WHERE upc = :upc")
       result = db.session.execute(check_query, {"upc": upc})
       existing_product = result.fetchone()


       if existing_product:
           # Оновлення існуючого товару
           update_query = text("""
               UPDATE store_product
               SET price = :price, quantity = quantity + :quantity,
                   expiration_date = :expiration_date,
                   is_promotional = :is_promotional,
                   promo_price = :promo_price
               WHERE upc = :upc
           """)


           db.session.execute(update_query, {
               "price": price,
               "quantity": quantity,
               "expiration_date": expiration_date,
               "is_promotional": is_promotional,
               "promo_price": promo_price,
               "upc": upc
           })


           flash("Інформацію про товар оновлено успішно!", "success")
       else:
           if not upc or not product_id or not price or not quantity:
               flash("Обов'язкові поля повинні бути заповнені.", "error")
               return redirect(url_for("views.add_storeproduct"))


           # Додавання нового товару
           insert_query = text("""
               INSERT INTO store_product (upc, product_id, price, promo_price, quantity, expiration_date, is_promotional)
               VALUES (:upc, :product_id, :price, :promo_price, :quantity, :expiration_date, :is_promotional)
           """)


           db.session.execute(insert_query, {
               "upc": upc,
               "product_id": product_id,
               "price": price,
               "promo_price": promo_price,
               "quantity": quantity,
               "expiration_date": expiration_date,
               "is_promotional": is_promotional
           })


           flash("Товар у магазині додано успішно!", "success")


       try:
           db.session.commit()
           return redirect(url_for('views.storeproducts'))
       except Exception as e:
           db.session.rollback()
           flash(f"Помилка при збереженні товару: {str(e)}", "error")
           return redirect(url_for("views.add_storeproduct"))


   # Отримання всіх продуктів для форми
   products_query = text("SELECT * FROM product")
   products_result = db.session.execute(products_query)
   products = [dict(row._mapping) for row in products_result.fetchall()]


   return render_template("add_storeproduct.html", user=current_user, products=products, storeproduct=storeproduct)




@views.route('/storeproducts/<string:upc>/delete', methods=['POST'])
@login_required
def delete_storeproduct(upc):
   # Перевіряємо, чи існує товар
   check_query = text("SELECT * FROM store_product WHERE upc = :upc")
   result = db.session.execute(check_query, {"upc": upc})
   store_product = result.fetchone()


   if not store_product:
       abort(404)


   # Видаляємо товар
   delete_query = text("DELETE FROM store_product WHERE upc = :upc")
   db.session.execute(delete_query, {"upc": upc})
   db.session.commit()


   flash("Товар у магазині успішно видалено", 'success')
   return redirect(url_for('views.storeproducts'))




@views.route('/storeproducts/fetch/<int:product_id>')
@login_required
def fetch_storeproduct(product_id):
   if current_user.position != 'Менеджер':
       abort(403)


   # Шукаємо товар за id продукту
   query = text("SELECT * FROM store_product WHERE product_id = :product_id")
   result = db.session.execute(query, {"product_id": product_id})
   storeproduct = result.fetchone()


   if storeproduct:
       # Форматуємо дату, якщо вона є
       expiration_date = None
       if storeproduct.expiration_date:
           expiration_date = storeproduct.expiration_date.isoformat() if hasattr(storeproduct.expiration_date,
                                                                                 'isoformat') else str(
               storeproduct.expiration_date)


       return jsonify({
           "exists": True,
           "upc": storeproduct.upc,
           "price": float(storeproduct.price),
           "expiration_date": expiration_date,
           "is_promotional": storeproduct.is_promotional
       })
   else:
       # Якщо товару ще немає в наявності — згенеруємо UPC
       last_upc_query = text("SELECT upc FROM store_product ORDER BY upc DESC LIMIT 1")
       last_upc_result = db.session.execute(last_upc_query)
       last_storeproduct = last_upc_result.fetchone()


       try:
           new_upc = str(int(last_storeproduct.upc) + 1) if last_storeproduct else "100000000000"
       except (ValueError, AttributeError):
           new_upc = "100000000000"


       return jsonify({
           "exists": False,
           "upc": new_upc
       })

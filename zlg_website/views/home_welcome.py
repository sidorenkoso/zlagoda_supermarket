from flask import render_template
from flask_login import login_required, current_user
from . import views
from flask import render_template, request, flash
from flask_login import login_required, current_user
from sqlalchemy import text
from . import views
from zlg_website import db

@views.route('/')
@login_required
def home():
    # Відображати сторінку головна (main.html)
    return render_template("main.html", user=current_user)


@views.route('/welcome')
@login_required
def welcome():
    # Відображати сторінку привітання (home.html)
    return render_template("home.html", user=current_user)


@views.route('/salesStatistics', methods=['GET'])
@login_required
def sales_statistics():
    query_results = None
    unused_products = None

    # Отримуємо вибрану категорію з параметрів URL
    selected_category = request.args.get('category')

    # SQL-запит 1 — Статистика клієнтів
    raw_sql = text("""
        SELECT
            c.card_number,
            CONCAT(c.last_name, ' ', c.first_name, ' ', c.middle_name) AS full_name,
            COUNT(r.receipt_number) AS receipt_count,
            ROUND(AVG(
                (SELECT SUM(ri.quantity * sp.price)
                 FROM receipt_item ri
                 JOIN store_product sp ON ri.upc = sp.upc
                 WHERE ri.receipt_number = r.receipt_number)
            ), 2) AS average_purchase_sum
        FROM customer_card c
        JOIN receipt r ON r.customer_card_number = c.card_number
        GROUP BY c.card_number, full_name
        HAVING COUNT(r.receipt_number) > 1
        ORDER BY average_purchase_sum DESC;
    """)

    # SQL-запит 2 — Товари у вибраній категорії, які не купували та не є акційними
    product_sql = text("""
        SELECT p.id, p.name, p.manufacturer, c.name AS category
        FROM product p
        JOIN category c ON p.category_number = c.category_number
        JOIN store_product sp ON sp.product_id = p.id
        WHERE c.name = :category_name
          AND NOT EXISTS (
              SELECT 1
              FROM receipt_item ri
              WHERE ri.upc = sp.upc
          )
          AND NOT EXISTS (
              SELECT 1
              FROM store_product sp2
              WHERE sp2.product_id = p.id AND sp2.is_promotional = TRUE
          );
    """)

    # Підключення до бази даних і виконання запитів
    with db.engine.connect() as connection:
        query_results = connection.execute(raw_sql).fetchall()

        # Якщо категорія вибрана, виконуємо другий запит для отримання непроданих неакційних товарів
        if selected_category:
            unused_products = connection.execute(product_sql, {"category_name": selected_category}).fetchall()
        else:
            unused_products = []

    # Список категорій для <select>
    categories = db.session.execute(text("SELECT category_number, name FROM category")).fetchall()

    return render_template(
        "salesStatistics.html",
        query_results=query_results,
        products=unused_products,  # Передаємо результат другого запиту як products
        categories=categories,
        selected_category=selected_category,
        user=current_user
    )

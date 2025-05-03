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

    # SQL-запит 1 Дарії Шин (багатотабличний з групуванням) — Статистика клієнтів
    raw_sql = text("""
        SELECT
            c.card_number,
            c.last_name || ' ' || c.first_name || ' ' || c.middle_name AS full_name,
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

    # SQL-запит 2 Дарії Шин (багатотабличний з подвійним запереченням, параметризований) — Товари у вибраній категорії, які не купували та не є акційними
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


@views.route('/cashierssql', methods=['GET'])
@login_required
def cashiers_sql():
    category_id = request.args.get('category_id', type=int)

    # SQL-запит 1 Сидоренко Софії (багатотабличний з групуванням) - Список касирів, які оформили понад 3 чеків, з підрахунком кількості чеків і середньою сумою чеку
    sql_1 = text("""
            SELECT
                e.last_name || ' ' || e.first_name || ' ' || e.middle_name AS cashier_name,
                COUNT(r.receipt_number) AS receipt_count,
                ROUND(AVG((
                    SELECT SUM(ri.quantity * sp.price)
                    FROM receipt_item ri
                    JOIN store_product sp ON sp.upc = ri.upc
                    WHERE ri.receipt_number = r.receipt_number
                )), 2) AS average_receipt_sum
            FROM employee e
            JOIN receipt r ON r.employee_id = e.id
            WHERE e.position = 'Касир'
            GROUP BY e.id
            HAVING COUNT(r.receipt_number) > 3
            ORDER BY average_receipt_sum DESC
        """)
    stats = db.session.execute(sql_1).mappings().all()

    categories = db.session.execute(
        text("SELECT category_number, name FROM category ORDER BY name")
    ).mappings().all()

    # SQL-запит 2 Дмитрохіної Альони (багатотабличний з подвійним запереченням, параметризований) - Знайти касирів, які ніколи не продавали товари певної категорії.
    product_results = []
    if category_id is not None:
        sql_2 = text("""
                SELECT DISTINCT
                    e.id,
                    e.last_name || ' ' || e.first_name || ' ' || e.middle_name AS cashier_name
                FROM employee e
                WHERE e.position = 'Касир'
                  AND e.id NOT IN (
                      SELECT r2.employee_id
                      FROM receipt r2
                      JOIN receipt_item ri2 ON ri2.receipt_number = r2.receipt_number
                      JOIN store_product sp2 ON sp2.upc = ri2.upc
                      JOIN product p2 ON p2.id = sp2.product_id
                      WHERE p2.category_number = :category_id
                  )
                ORDER BY e.id
                LIMIT 5
            """)
        product_results = db.session.execute(sql_2, {'category_id': category_id}).mappings().all()

    return render_template("cashierssql.html",
                           user=current_user,
                           stats=stats,
                           categories=categories,
                           product_results=product_results,
                           category_id=category_id)


@views.route('/clientssql', methods=['GET'])
@login_required
def clients_sql():
    min_discount = request.args.get('min_discount', default=0.0, type=float)
    # SQL-запит 1 Дмитрохіної Альони (багатотабличний з групуванням) - Показати ТОП-5 клієнтів (за кількістю чеків), які зробили більше 1 покупки, включаючи повне ім’я клієнта, кількість чеків та середню суму покупки.
    sql_1 = text("""
                SELECT
    c.card_number,
    c.last_name || ' ' || c.first_name || ' ' || c.middle_name AS full_name,
    COUNT(DISTINCT r.receipt_number) AS receipt_count,
    ROUND(AVG(
        (SELECT SUM(ri.quantity * sp.price)
         FROM receipt_item ri
         JOIN store_product sp ON ri.upc = sp.upc
         WHERE ri.receipt_number = r.receipt_number)
    ), 2) AS avg_purchase_sum
FROM customer_card c
JOIN receipt r ON r.customer_card_number = c.card_number
GROUP BY c.card_number
HAVING COUNT(DISTINCT r.receipt_number) > 1
ORDER BY avg_purchase_sum DESC
LIMIT 5;
            """)
    top_clients = db.session.execute(sql_1).mappings().all()

    # SQL-запит 2 Сидоренко Софії (багатотабличний з подвійним запереченням, параметризований) - Знайти товари, які ніколи не купувалися клієнтами та які не мають знижки
    sql_2 = text("""
SELECT DISTINCT p.name
FROM product p
JOIN store_product sp ON sp.product_id = p.id
JOIN receipt_item ri ON ri.upc = sp.upc
JOIN receipt r ON r.receipt_number = ri.receipt_number
JOIN customer_card c ON c.card_number = r.customer_card_number
WHERE p.id NOT IN (
    SELECT p2.id
    FROM product p2
    JOIN store_product sp2 ON sp2.product_id = p2.id
    JOIN receipt_item ri2 ON ri2.upc = sp2.upc
    JOIN receipt r2 ON r2.receipt_number = ri2.receipt_number
    JOIN customer_card c2 ON c2.card_number = r2.customer_card_number
    WHERE c2.discount_percent < :min_discount OR c2.discount_percent IS NULL
)
LIMIT 5;""")
    unsold_products = db.session.execute(sql_2, {'min_discount': min_discount}).mappings().all()

    return render_template(
        "clientssql.html",
        user=current_user,
        top_clients=top_clients,
        unsold_products=unsold_products,
        min_discount=min_discount
    )

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
import os
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from sqlalchemy import text

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'zlagoda'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, DB_NAME)}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    # Import the model classes after db is defined
    from .models import Employee, Category, Product

    with app.app_context():
        if database_is_empty(app):
            create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        # Since we're using SQL directly, we need to call the get_by_id method
        return Employee.get_by_id(id)

    return app


def create_database(app):
    db_path = 'instance/' + DB_NAME

    if not path.exists(db_path):
        os.makedirs('instance', exist_ok=True)
        with app.app_context():
            # Create tables using raw SQL as done in seed.py
            # Recreate the database structure
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS employee (
                    id INTEGER PRIMARY KEY,
                    last_name TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    middle_name TEXT,
                    position TEXT NOT NULL,
                    salary REAL NOT NULL,
                    start_date DATE NOT NULL,
                    birth_date DATE NOT NULL,
                    phone TEXT NOT NULL,
                    city TEXT NOT NULL,
                    street TEXT NOT NULL,
                    postal_code TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE
                )
            """))

            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS category (
                    category_number INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """))

            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS product (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    specifications TEXT,
                    category_number INTEGER NOT NULL,
                    FOREIGN KEY (category_number) REFERENCES category (category_number)
                )
            """))

            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS store_product (
                    upc TEXT PRIMARY KEY,
                    price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    expiration_date DATE,
                    is_promotional BOOLEAN DEFAULT FALSE,
                    promo_price REAL,
                    product_id INTEGER NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES product (id)
                )
            """))

            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS customer_card (
                    card_number TEXT PRIMARY KEY,
                    last_name TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    middle_name TEXT,
                    phone TEXT NOT NULL,
                    city TEXT NOT NULL,
                    street TEXT NOT NULL,
                    postal_code TEXT NOT NULL,
                    discount_percent REAL DEFAULT 0
                )
            """))

            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS receipt (
                    receipt_number TEXT PRIMARY KEY,
                    date TIMESTAMP NOT NULL,
                    customer_card_number TEXT,
                    employee_id INTEGER NOT NULL,
                    FOREIGN KEY (customer_card_number) REFERENCES customer_card (card_number),
                    FOREIGN KEY (employee_id) REFERENCES employee (id)
                )
            """))

            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS receipt_item (
                    id INTEGER PRIMARY KEY,
                    receipt_number TEXT NOT NULL,
                    upc TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    FOREIGN KEY (receipt_number) REFERENCES receipt (receipt_number),
                    FOREIGN KEY (upc) REFERENCES store_product (upc)
                )
            """))

            # Create a default admin user
            password = generate_password_hash("admin123")
            db.session.execute(text("""
                INSERT INTO employee (id, last_name, first_name, middle_name, position, salary, 
                start_date, birth_date, phone, city, street, postal_code, password, email)
                VALUES (100, 'Admin', 'Admin', '', 'Менеджер', 30000, '2022-01-01', '1990-01-01', 
                '+380501234567', 'Київ', 'Хрещатик', '01001', :password, 'admin@zlagoda.com')
            """), {"password": password})

            db.session.commit()
            print('Database created')
    else:
        print('Database already exists')


def database_is_empty(app):
    with app.app_context():
        # Check if the employee table has any entries
        result = db.session.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='employee'")).fetchone()
        if result and result[0] > 0:
            # Table exists, check if it has records
            count = db.session.execute(text("SELECT COUNT(*) FROM employee")).fetchone()
            return count[0] == 0
        return True  # Table doesn't exist, so database is considered empty
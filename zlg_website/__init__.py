from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
import os
from flask_login import LoginManager, login_manager
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'zlagoda'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.instance_path, DB_NAME)}'

    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import Employee

    with app.app_context():
        if database_is_empty():
            create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Employee.query.get(int(id))

    return app


def create_database(app):
    if not path.exists('zlg_website/' + DB_NAME):
        with app.app_context():
            db.create_all()
        hashed = generate_password_hash("password")
        print('Database created')
    else:
        print('Database already exists')


def database_is_empty():
    from .models import Employee, Product, Category  # тощо — ключові таблиці
    return (
        Employee.query.first() is None and
        Product.query.first() is None and
        Category.query.first() is None
    )
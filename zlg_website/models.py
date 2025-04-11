from . import db
from sqlalchemy.sql import func
from flask_login import UserMixin
from datetime import datetime, timedelta

# Працівник
class Employee(db.Model, UserMixin):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    position = db.Column(db.String(100))
    salary = db.Column(db.Float)
    start_date = db.Column(db.Date)
    birth_date = db.Column(db.Date)
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100))
    street = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    password = db.Column(db.String(10000))
    email = db.Column(db.String(100), unique=True)

# Категорія
class Category(db.Model):
    __tablename__ = 'category'
    category_number = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# Товар
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    manufacturer = db.Column(db.String(100))
    specifications = db.Column(db.Text)
    category_number = db.Column(db.Integer, db.ForeignKey('category.category_number'))
    category = db.relationship('Category', backref='products')

# Товар у магазині
class StoreProduct(db.Model):
    tablename = 'store_product'

    upc = db.Column(db.String(12), primary_key=True)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    expiration_date = db.Column(db.Date)  # НОВЕ: дата придатності
    is_promotional = db.Column(db.Boolean, default=False)  # Додано поле для акційного статусу
    promo_price = db.Column(db.Float)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product', backref='store_items')

    @property
    def calculate_promotional(self):
        """Визначає, чи є товар акційним: якщо термін збігає і кількість велика."""
        soon_expiring = self.expiration_date and self.expiration_date <= datetime.now().date() + timedelta(days=7)
        high_quantity = self.quantity > 30
        return soon_expiring and high_quantity

    @property
    def calculate_promo_price(self):
        """Ціна акційного товару зі знижкою 20%"""
        return round(self.price * 0.8, 2) if self.is_promotional else self.price

    @calculate_promotional.setter
    def calculate_promotional(self, value):
        self.calculate_promotional = value

    @calculate_promo_price.setter
    def calculate_promo_price(self, value):
        self.calculate_promo_price = value


# Карта клієнта
class CustomerCard(db.Model):
    __tablename__ = 'customer_card'
    card_number = db.Column(db.String(20), primary_key=True)
    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    city = db.Column(db.String(100), nullable=True)
    street = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    discount_percent = db.Column(db.Float)

# Чек
class Receipt(db.Model):
    __tablename__ = 'receipt'
    receipt_number = db.Column(db.String(20), primary_key=True)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    # Загальна сума та ПДВ розраховуються при потребі
    customer_card_number = db.Column(db.String(20), db.ForeignKey('customer_card.card_number'), nullable=True)
    customer_card = db.relationship('CustomerCard', backref='receipts')
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'))
    employee = db.relationship('Employee', backref='receipts')

    @property
    def total_sum(self):
        return round(sum(item.quantity * item.store_product.price for item in self.items), 2)

    @property
    def vat(self):
        return round(self.total_sum * 0.2, 2)

# Зв'язок товарів і чеків (позиції в чеку)
class ReceiptItem(db.Model):
    __tablename__ = 'receipt_item'
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(20), db.ForeignKey('receipt.receipt_number'))
    upc = db.Column(db.String(12), db.ForeignKey('store_product.upc'))
    quantity = db.Column(db.Integer)
    receipt = db.relationship('Receipt', backref='items')
    store_product = db.relationship('StoreProduct', backref='receipt_items')

from . import db
from sqlalchemy.sql import func
from flask_login import UserMixin

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
    password = db.Column(db.String(100))
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
    __tablename__ = 'store_product'
    upc = db.Column(db.String(12), primary_key=True)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    is_promotional = db.Column(db.Boolean)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    product = db.relationship('Product', backref='store_items')

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

# Зв'язок товарів і чеків (позиції в чеку)
class ReceiptItem(db.Model):
    __tablename__ = 'receipt_item'
    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(20), db.ForeignKey('receipt.receipt_number'))
    upc = db.Column(db.String(12), db.ForeignKey('store_product.upc'))
    quantity = db.Column(db.Integer)
    receipt = db.relationship('Receipt', backref='items')
    store_product = db.relationship('StoreProduct', backref='receipt_items')

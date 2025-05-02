from flask_login import UserMixin
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy.sql import text
from . import db




# Класи для зберігання даних, не використовуючи ORM
@dataclass
class Employee(UserMixin):
   id: int
   last_name: str
   first_name: str
   middle_name: str
   position: str
   salary: float
   start_date: datetime
   birth_date: datetime
   phone: str
   city: str
   street: str
   postal_code: str
   password: str
   email: str


   @property
   def full_name(self):
       parts = [self.last_name, self.first_name, self.middle_name]
       return " ".join(part for part in parts if part)


   @property
   def address(self):
       return f"{self.city}, {self.street}, {self.postal_code}"


   # Метод для отримання всіх працівників з бази даних
   @staticmethod
   def get_all():
       employees = []
       result = db.session.execute(text("SELECT * FROM employee ORDER BY id"))
       for row in result:
           employees.append(Employee(
               id=row.id,
               last_name=row.last_name,
               first_name=row.first_name,
               middle_name=row.middle_name,
               position=row.position,
               salary=row.salary,
               start_date=row.start_date,
               birth_date=row.birth_date,
               phone=row.phone,
               city=row.city,
               street=row.street,
               postal_code=row.postal_code,
               password=row.password,
               email=row.email
           ))
       return employees


   # Метод для отримання працівника за ID
   @staticmethod
   def get_by_id(id):
       result = db.session.execute(text("SELECT * FROM employee WHERE id = :id"), {"id": id}).fetchone()
       if result:
           return Employee(
               id=result.id,
               last_name=result.last_name,
               first_name=result.first_name,
               middle_name=result.middle_name,
               position=result.position,
               salary=result.salary,
               start_date=result.start_date,
               birth_date=result.birth_date,
               phone=result.phone,
               city=result.city,
               street=result.street,
               postal_code=result.postal_code,
               password=result.password,
               email=result.email
           )
       return None


   # Метод для отримання працівника за email (для аутентифікації)
   @staticmethod
   def get_by_email(email):
       result = db.session.execute(text("SELECT * FROM employee WHERE email = :email"), {"email": email}).fetchone()
       if result:
           return Employee(
               id=result.id,
               last_name=result.last_name,
               first_name=result.first_name,
               middle_name=result.middle_name,
               position=result.position,
               salary=result.salary,
               start_date=result.start_date,
               birth_date=result.birth_date,
               phone=result.phone,
               city=result.city,
               street=result.street,
               postal_code=result.postal_code,
               password=result.password,
               email=result.email
           )
       return None


   # Метод для фільтрації за посадою
   @staticmethod
   def filter_by_position(position):
       employees = []
       result = db.session.execute(text("SELECT * FROM employee WHERE position = :position"), {"position": position})
       for row in result:
           employees.append(Employee(
               id=row.id,
               last_name=row.last_name,
               first_name=row.first_name,
               middle_name=row.middle_name,
               position=row.position,
               salary=row.salary,
               start_date=row.start_date,
               birth_date=row.birth_date,
               phone=row.phone,
               city=row.city,
               street=row.street,
               postal_code=row.postal_code,
               password=row.password,
               email=row.email
           ))
       return employees


   # Метод для сортування за прізвищем
   @staticmethod
   def get_all_sorted_by_lastname(order='asc'):
       employees = []
       order_clause = "ASC" if order == 'asc' else "DESC"
       result = db.session.execute(text(f"SELECT * FROM employee ORDER BY last_name {order_clause}"))
       for row in result:
           employees.append(Employee(
               id=row.id,
               last_name=row.last_name,
               first_name=row.first_name,
               middle_name=row.middle_name,
               position=row.position,
               salary=row.salary,
               start_date=row.start_date,
               birth_date=row.birth_date,
               phone=row.phone,
               city=row.city,
               street=row.street,
               postal_code=row.postal_code,
               password=row.password,
               email=row.email
           ))
       return employees


   # Метод для додавання нового працівника
   @staticmethod
   def add(id, last_name, first_name, middle_name, position, salary, start_date, birth_date, phone, city, street,
           postal_code, password, email):
       try:
           db.session.execute(text("""
               INSERT INTO employee (id, last_name, first_name, middle_name, position, salary, start_date, birth_date, phone, city, street, postal_code, password, email)
               VALUES (:id, :last_name, :first_name, :middle_name, :position, :salary, :start_date, :birth_date, :phone, :city, :street, :postal_code, :password, :email)
           """), {
               'id': id,
               'last_name': last_name,
               'first_name': first_name,
               'middle_name': middle_name,
               'position': position,
               'salary': salary,
               'start_date': start_date,
               'birth_date': birth_date,
               'phone': phone,
               'city': city,
               'street': street,
               'postal_code': postal_code,
               'password': password,
               'email': email
           })
           db.session.commit()
           return True
       except Exception as e:
           db.session.rollback()
           raise e


   # Метод для оновлення даних працівника
   @staticmethod
   def update(id, last_name, first_name, middle_name, position, salary, start_date, birth_date, phone, city, street,
              postal_code, email, password=None):
       try:
           if password:
               db.session.execute(text("""
                   UPDATE employee
                   SET last_name = :last_name, first_name = :first_name, middle_name = :middle_name, position = :position,
                       salary = :salary, start_date = :start_date, birth_date = :birth_date, phone = :phone,
                       city = :city, street = :street, postal_code = :postal_code, email = :email, password = :password
                   WHERE id = :id
               """), {
                   'id': id,
                   'last_name': last_name,
                   'first_name': first_name,
                   'middle_name': middle_name,
                   'position': position,
                   'salary': salary,
                   'start_date': start_date,
                   'birth_date': birth_date,
                   'phone': phone,
                   'city': city,
                   'street': street,
                   'postal_code': postal_code,
                   'email': email,
                   'password': password
               })
           else:
               db.session.execute(text("""
                   UPDATE employee
                   SET last_name = :last_name, first_name = :first_name, middle_name = :middle_name, position = :position,
                       salary = :salary, start_date = :start_date, birth_date = :birth_date, phone = :phone,
                       city = :city, street = :street, postal_code = :postal_code, email = :email
                   WHERE id = :id
               """), {
                   'id': id,
                   'last_name': last_name,
                   'first_name': first_name,
                   'middle_name': middle_name,
                   'position': position,
                   'salary': salary,
                   'start_date': start_date,
                   'birth_date': birth_date,
                   'phone': phone,
                   'city': city,
                   'street': street,
                   'postal_code': postal_code,
                   'email': email
               })
           db.session.commit()
           return True
       except Exception as e:
           db.session.rollback()
           raise e


   # Метод для видалення працівника
   @staticmethod
   def delete(id):
       try:
           db.session.execute(text("DELETE FROM employee WHERE id = :id"), {"id": id})
           db.session.commit()
           return True
       except Exception as e:
           db.session.rollback()
           raise e


   # Метод для перевірки неможливості виконувати функції касира
   @staticmethod
   def is_cashier(id):
       result = db.session.execute(text("SELECT position FROM employee WHERE id = :id"), {"id": id}).fetchone()
       return result.position == 'Касир' if result else False




@dataclass
class Category:
   category_number: int
   name: str


   @staticmethod
   def get_all():
       categories = []
       result = db.session.execute(text("SELECT * FROM category"))
       for row in result:
           categories.append(Category(
               category_number=row.category_number,
               name=row.name
           ))
       return categories


   @staticmethod
   def get_by_id(category_number):
       result = db.session.execute(text("SELECT * FROM category WHERE category_number = :category_number"),
                                   {"category_number": category_number}).fetchone()
       if result:
           return Category(
               category_number=result.category_number,
               name=result.name
           )
       return None




@dataclass
class Product:
   id: int
   name: str
   manufacturer: str
   specifications: str
   category_number: int


   @staticmethod
   def get_all():
       products = []
       result = db.session.execute(text("""
           SELECT p.*, c.name as category_name
           FROM product p
           JOIN category c ON p.category_number = c.category_number
       """))
       for row in result:
           products.append(Product(
               id=row.id,
               name=row.name,
               manufacturer=row.manufacturer,
               specifications=row.specifications,
               category_number=row.category_number
           ))
       return products


   @staticmethod
   def get_by_id(id):
       result = db.session.execute(text("""
           SELECT p.*, c.name as category_name
           FROM product p
           JOIN category c ON p.category_number = c.category_number
           WHERE p.id = :id
       """), {"id": id}).fetchone()
       if result:
           return Product(
               id=result.id,
               name=result.name,
               manufacturer=result.manufacturer,
               specifications=result.specifications,
               category_number=result.category_number
           )
       return None




@dataclass
class StoreProduct:
   upc: str
   price: float
   quantity: int
   expiration_date: datetime
   is_promotional: bool
   promo_price: float
   product_id: int


   @staticmethod
   def get_all():
       store_products = []
       result = db.session.execute(text("""
           SELECT sp.*, p.name as product_name
           FROM store_product sp
           JOIN product p ON sp.product_id = p.id
       """))
       for row in result:
           store_products.append(StoreProduct(
               upc=row.upc,
               price=row.price,
               quantity=row.quantity,
               expiration_date=row.expiration_date,
               is_promotional=row.is_promotional,
               promo_price=row.promo_price,
               product_id=row.product_id
           ))
       return store_products


   @staticmethod
   def get_by_upc(upc):
       result = db.session.execute(text("""
           SELECT sp.*, p.name as product_name
           FROM store_product sp
           JOIN product p ON sp.product_id = p.id
           WHERE sp.upc = :upc
       """), {"upc": upc}).fetchone()
       if result:
           return StoreProduct(
               upc=result.upc,
               price=result.price,
               quantity=result.quantity,
               expiration_date=result.expiration_date,
               is_promotional=result.is_promotional,
               promo_price=result.promo_price,
               product_id=result.product_id
           )
       return None


   def calculate_promotional(self):
       """Визначає, чи є товар акційним: якщо термін збігає і кількість велика."""
       soon_expiring = self.expiration_date and self.expiration_date <= datetime.now().date() + timedelta(days=7)
       high_quantity = self.quantity > 30
       return soon_expiring and high_quantity


   def calculate_promo_price(self):
       """Ціна акційного товару зі знижкою 20%"""
       return round(self.price * 0.8, 2) if self.is_promotional else self.price




@dataclass
class CustomerCard:
   card_number: str
   last_name: str
   first_name: str
   middle_name: str
   phone: str
   city: str
   street: str
   postal_code: str
   discount_percent: float


   @staticmethod
   def get_all():
       customer_cards = []
       result = db.session.execute(text("SELECT * FROM customer_card"))
       for row in result:
           customer_cards.append(CustomerCard(
               card_number=row.card_number,
               last_name=row.last_name,
               first_name=row.first_name,
               middle_name=row.middle_name,
               phone=row.phone,
               city=row.city,
               street=row.street,
               postal_code=row.postal_code,
               discount_percent=row.discount_percent
           ))
       return customer_cards


   @staticmethod
   def get_by_card_number(card_number):
       result = db.session.execute(text("SELECT * FROM customer_card WHERE card_number = :card_number"),
                                   {"card_number": card_number}).fetchone()
       if result:
           return CustomerCard(
               card_number=result.card_number,
               last_name=result.last_name,
               first_name=result.first_name,
               middle_name=result.middle_name,
               phone=result.phone,
               city=result.city,
               street=result.street,
               postal_code=result.postal_code,
               discount_percent=result.discount_percent
           )
       return None




@dataclass
class Receipt:
   receipt_number: str
   date: datetime
   customer_card_number: str
   employee_id: int


   @staticmethod
   def get_all():
       receipts = []
       result = db.session.execute(text("""
           SELECT r.*, e.last_name as employee_last_name, e.first_name as employee_first_name,
                  cc.last_name as customer_last_name, cc.first_name as customer_first_name
           FROM receipt r
           JOIN employee e ON r.employee_id = e.id
           LEFT JOIN customer_card cc ON r.customer_card_number = cc.card_number
       """))
       for row in result:
           receipts.append(Receipt(
               receipt_number=row.receipt_number,
               date=row.date,
               customer_card_number=row.customer_card_number,
               employee_id=row.employee_id
           ))
       return receipts


   @staticmethod
   def get_by_receipt_number(receipt_number):
       result = db.session.execute(text("""
           SELECT r.*, e.last_name as employee_last_name, e.first_name as employee_first_name,
                  cc.last_name as customer_last_name, cc.first_name as customer_first_name
           FROM receipt r
           JOIN employee e ON r.employee_id = e.id
           LEFT JOIN customer_card cc ON r.customer_card_number = cc.card_number
           WHERE r.receipt_number = :receipt_number
       """), {"receipt_number": receipt_number}).fetchone()
       if result:
           return Receipt(
               receipt_number=result.receipt_number,
               date=result.date,
               customer_card_number=result.customer_card_number,
               employee_id=result.employee_id
           )
       return None


   def get_total_sum(self):
       result = db.session.execute(text("""
           SELECT SUM(ri.quantity * sp.price) as total_sum
           FROM receipt_item ri
           JOIN store_product sp ON ri.upc = sp.upc
           WHERE ri.receipt_number = :receipt_number
       """), {"receipt_number": self.receipt_number}).fetchone()


       return round(result.total_sum, 2) if result and result.total_sum else 0


   def get_vat(self):
       total_sum = self.get_total_sum()
       return round(total_sum * 0.2, 2)


   @staticmethod
   def validate_cashier_only(employee_id):
       result = db.session.execute(text("SELECT position FROM employee WHERE id = :id"),
                                   {"id": employee_id}).fetchone()
       if result and result.position != 'Касир':
           raise ValueError("Чек може бути створений тільки касиром.")
       return True




@dataclass
class ReceiptItem:
   id: int
   receipt_number: str
   upc: str
   quantity: int


   @staticmethod
   def get_by_receipt_number(receipt_number):
       items = []
       result = db.session.execute(text("""
           SELECT ri.*, sp.price, p.name as product_name
           FROM receipt_item ri
           JOIN store_product sp ON ri.upc = sp.upc
           JOIN product p ON sp.product_id = p.id
           WHERE ri.receipt_number = :receipt_number
       """), {"receipt_number": receipt_number})


       for row in result:
           items.append(ReceiptItem(
               id=row.id,
               receipt_number=row.receipt_number,
               upc=row.upc,
               quantity=row.quantity
           ))
       return items

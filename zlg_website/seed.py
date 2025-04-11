from zlg_website import create_app, db  # Імпортуємо додаток і базу даних з вашого додатку
from zlg_website.models import Employee, Category, Product, StoreProduct, CustomerCard, Receipt, ReceiptItem
from faker import Faker
from random import randint, uniform, choice
from datetime import datetime
from werkzeug.security import generate_password_hash


fake = Faker('uk_UA')

# Створюємо додаток
app = create_app()

def seed_database(n_employees=5, n_categories=3, n_products=10, n_customers=5, n_receipts=5):
    with app.app_context():  # Додано контекст додатку
        db.drop_all()  # Видаляємо таблиці (якщо вони існують)
        db.create_all()  # Створюємо таблиці (якщо ще не створені)

        print("Seeding database...")

        # Категорії
        categories = []
        for i in range(n_categories):
            cat = Category(category_number=i+1, name=fake.word().capitalize())
            db.session.add(cat)
            categories.append(cat)

        # Працівники
        employees = []
        for _ in range(n_employees):
            emp = Employee(
                last_name=fake.last_name(),
                first_name=fake.first_name(),
                middle_name=fake.first_name(),
                position=choice(['Касир', 'Менеджер']),
                salary=round(uniform(12000, 25000), 2),
                start_date=fake.date_between(start_date='-5y', end_date='-1y'),
                birth_date=fake.date_between(start_date='-50y', end_date='-20y'),
                phone=fake.msisdn(),
                city=fake.city(),
                street=fake.street_name(),
                postal_code=fake.postcode(),
                email=fake.email(),
                password='password'  # У тестах не хешуємо
            )
            db.session.add(emp)
            employees.append(emp)


        password = 'password'

        # Додати нового працівника
        new_employee = Employee(
            last_name='Іванов',
            first_name='Іван',
            middle_name='Іванович',
            position='Касир',
            salary=15000.00,
            start_date=datetime(2020, 1, 1),
            birth_date=datetime(1990, 5, 15),
            phone='+380123456789',
            city='Київ',
            street='Вул. Шевченка',
            postal_code='01001',
            email='ivanov@example.com',
            password='password'
        )
        db.session.add(new_employee)
        employees.append(new_employee)

        employees_in_db = Employee.query.all()
        print(f"Employees in DB: {len(employees_in_db)}")
        for emp in employees_in_db:
            print(emp.first_name, emp.last_name)

        # Товари
        products = []
        for _ in range(n_products):
            product = Product(
                name=fake.word().capitalize(),
                manufacturer=fake.company(),
                specifications=fake.text(max_nb_chars=50),
                category=choice(categories)
            )
            db.session.add(product)
            products.append(product)

        # Товари у магазині
        store_products = []
        for prod in products:
            sp = StoreProduct(
                upc=fake.unique.ean(length=13),
                price=round(uniform(50, 5000), 2),
                quantity=randint(1, 50),
                is_promotional=choice([True, False]),
                product=prod
            )
            db.session.add(sp)
            store_products.append(sp)

        # Клієнтські картки
        customers = []
        for _ in range(n_customers):
            card = CustomerCard(
                card_number=fake.unique.bothify(text='####-####'),
                last_name=fake.last_name(),
                first_name=fake.first_name(),
                middle_name=fake.first_name(),
                phone=fake.msisdn(),
                city=choice([fake.city(), None]),
                street=choice([fake.street_name(), None]),
                postal_code=choice([fake.postcode(), None]),
                discount_percent=round(uniform(0, 10), 2)
            )
            db.session.add(card)
            customers.append(card)

        # Чеки
        for _ in range(n_receipts):
            receipt = Receipt(
                receipt_number=fake.unique.bothify(text='R####'),
                date=fake.date_time_between(start_date='-1y', end_date='now'),
                customer_card=choice(customers),
                employee=choice(employees)
            )
            db.session.add(receipt)

            # Позиції чеку
            items_count = randint(1, 5)
            for _ in range(items_count):
                item = ReceiptItem(
                    receipt=receipt,
                    store_product=choice(store_products),
                    quantity=randint(1, 5)
                )
                db.session.add(item)


if __name__ == '__main__':
    seed_database()

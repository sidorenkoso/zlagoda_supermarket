from zlg_website import create_app, db
from faker import Faker
from random import randint, uniform, choice
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import json
import transliterate
from sqlalchemy import text
import random

fake = Faker('uk_UA')

# Створюємо додаток
app = create_app()


def generate_expiration_date():
    # Генеруємо випадкову кількість місяців від 1 до 12
    months_to_add = random.randint(1, 12)

    # Поточна дата
    current_date = datetime.now()

    # Отримуємо нову дату через додавання місяців вручну
    new_month = current_date.month + months_to_add
    new_year = current_date.year + (new_month - 1) // 12  # додаємо до року, якщо місяці перевищують 12
    new_month = new_month % 12 or 12  # забезпечуємо, щоб місяць був від 1 до 12

    # Визначаємо день місяця
    day = min(current_date.day,
              [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][new_month - 1])  # максимальний день місяця

    # Створюємо нову дату
    expiration_date = datetime(new_year, new_month, day)
    return expiration_date.date()


def generate_unique_password(first_name, last_name, birth_year):
    first = transliterate.translit(first_name[:3], reversed=True).lower()
    last = transliterate.translit(last_name[:3], reversed=True).lower()
    return f"{first}{last}{birth_year}"


def generate_email(first_name, last_name):
    # Транслітерація імені та прізвища в латинку
    first = transliterate.translit(first_name, 'uk', reversed=True).lower()
    last = transliterate.translit(last_name, 'uk', reversed=True).lower()

    # Формуємо email
    return f"{first}.{last}@gmail.com"


def generate_ua_phone():
    return '+380' + ''.join([str(randint(0, 9)) for _ in range(9)])


def generate_characteristic_value(characteristic):
    if characteristic == 'вага':
        return f"{uniform(0.1, 5):.2f} кг"
    elif characteristic == 'об\'єм':
        return f"{uniform(250, 2000):.0f} мл"
    elif characteristic == 'тип':
        return choice(['газована', 'негазована', 'мінеральна', 'темне', 'світле'])
    elif characteristic == 'міцність':
        return f"{uniform(0.5, 12):.1f}%"
    elif characteristic == 'жирність':
        return f"{uniform(0.1, 10):.1f}%"
    elif characteristic == 'вміст какао':
        return f"{choice([30, 50, 70, 85])}%"
    elif characteristic == 'сорт':
        return choice(['Гала', 'Голден', 'Ред Делішес', 'Фуджі'])
    elif characteristic == 'походження':
        return choice(['Україна', 'Польща', 'Італія', 'Іспанія'])
    elif characteristic == 'м\'ясо':
        return choice(['свинина', 'яловичина', 'курятина', 'індичка'])
    # Додати інші або залишити за замовчуванням
    else:
        return "—"


def seed_database(n_employees=5, n_categories=3, n_products=10, n_customers=5, n_receipts=5):
    with app.app_context():  # Додано контекст додатку
        # Видаляємо таблиці (якщо вони існують)
        db.session.execute(text("DROP TABLE IF EXISTS receipt_item"))
        db.session.execute(text("DROP TABLE IF EXISTS receipt"))
        db.session.execute(text("DROP TABLE IF EXISTS store_product"))
        db.session.execute(text("DROP TABLE IF EXISTS product"))
        db.session.execute(text("DROP TABLE IF EXISTS category"))
        db.session.execute(text("DROP TABLE IF EXISTS customer_card"))
        db.session.execute(text("DROP TABLE IF EXISTS employee"))
        db.session.commit()

        # Створюємо таблиці
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

        db.session.commit()

        middle_name_male = [
            "Олександрович", "Іванович", "Володимирович", "Петрович", "Юрійович",
            "Максимович", "Анатолійович", "Сергійович", "Васильович", "Олегович"
        ]
        middle_name_female = [
            "Олександрівна", "Іванівна", "Володимирівна", "Петрівна", "Юріївна",
            "Максимівна", "Анатоліївна", "Сергіївна", "Василівна", "Олегівна"
        ]
        last_names = [
            "Петренко", "Сидоренко", "Коваль", "Бондаренко",
            "Шевченко", "Мороз", "Гончаренко", "Ткаченко", "Рибак",
            "Ковальчук", "Левченко", "Бондаренко", "Савченко",
            "Яценко", "Дорошенко", "Курах", "Бабенко", "Черненко"
        ]

        # Продукти за категоріями
        product_categories = [
            ('Продукти харчування', ['вага', 'склад']),
            ('Напої', ['об\'єм', 'склад']),
            ('Солодощі', ['вага', 'склад']),
            ('Молочні продукти', ['вага', 'склад']),
            ('М\'ясні продукти', ['вага', 'склад']),
            ('Кондитерські вироби', ['вага', 'склад']),
            ('Заморожені продукти', ['вага', 'склад']),
            ('Зернові та бобові', ['вага', 'склад']),
            ('Овочі та фрукти', ['вага']),
            ('Спеції та приправи', ['вага', 'склад'])
        ]

        # Виробники для різних продуктів
        manufacturer_examples = {
            'Продукти харчування': ['Хлібозавод', 'Галичина', 'Рудь', 'АВК', 'Слов\'яночка'],
            'Напої': ['Оболонь', 'Старий Млин', 'Рудь', 'Coca-Cola', 'Pepsi'],
            'Солодощі': ['Київська кондитерська фабрика', 'Конті', 'Roshen', 'АВК', 'Чупа Чупс'],
            'Молочні продукти': ['Молокія', 'Галичина', 'Терра', 'Данон', 'Рудь'],
            'М\'ясні продукти': ['Ічня', 'М\'ясна компанія', 'М\'ясокомбінат', 'Колос', 'М\'ясо України'],
            'Кондитерські вироби': ['Київська кондитерська фабрика', 'Roshen', 'Конті', 'Світоч', 'Чупа Чупс'],
            'Заморожені продукти': ['Макс Фуд', 'Імперія смаку', 'Заморожені продукти', 'Грін Ленд', 'Люкс-Продукт'],
            'Зернові та бобові': ['Гречка', 'Лісовий шлях', 'Органік', 'Біла квасоля', 'Преміум'],
            'Овочі та фрукти': ['Фрукта', 'Овочі України', 'Еко-Продукт', 'Зелені овочі', 'Фрукти з України'],
            'Спеції та приправи': ['Смакота', 'Скороход', 'Сезон', 'Грінфуд', 'Еко-Приправа']
        }

        product_examples = {
            'Продукти харчування': [
                ('Хліб', 'пшеничне борошно, вода, дріжджі, сіль'),
                ('Макарони', 'пшеничне борошно, вода'),
                ('Каша', 'гречана крупа'),
                ('Рис', 'шліфований рис'),
                ('Сіль', 'кам\'яна сіль')
            ],
            'Напої': [
                ('Вода', 'вода питна'),
                ('Сік', 'яблучний сік, цукор, вітамін C'),
                ('Квас', 'вода, житній солод, цукор, дріжджі'),
                ('Кока-Кола', 'вода, цукор, барвник, кофеїн, ароматизатори'),
                ('Пиво', 'вода, ячмінний солод, хміль, дріжджі')
            ],
            'Солодощі': [
                ('Шоколад', 'какао, молоко, цукор, лецитин'),
                ('Цукерки', 'цукор, патока, ароматизатори'),
                ('Печиво', 'борошно, масло, яйця, цукор'),
                ('Пиріжки', 'борошно, начинка (яблуко/вишня), цукор'),
                ('Маршмеллоу', 'цукор, вода, желатин, ароматизатори')
            ],
            'Молочні продукти': [
                ('Молоко', 'пастеризоване молоко'),
                ('Сметана', 'вершки, закваска'),
                ('Творог', 'молоко, закваска'),
                ('Йогурт', 'молоко, йогуртна закваска, фруктове пюре'),
                ('Сир', 'молоко, закваска, сіль')
            ],
            'М\'ясні продукти': [
                ('Ковбаса', 'м\'ясо свинини, сіль, спеції, нітрит натрію'),
                ('М\'ясо', 'яловичина / свинина'),
                ('Шинка', 'м\'ясо свинини, сіль, спеції'),
                ('Печінка', 'свиняча печінка'),
                ('Сосиски', 'м\'ясо, спеції, вода, сіль')
            ],
            'Кондитерські вироби': [
                ('Торт', 'борошно, яйця, крем, цукор, какао'),
                ('Печиво', 'борошно, цукор, масло'),
                ('Пиріжки', 'борошно, фруктова начинка'),
                ('Кекси', 'борошно, яйця, масло, розпушувач'),
                ('Булочки', 'борошно, дріжджі, цукор, молоко')
            ],
            'Заморожені продукти': [
                ('Заморожена риба', 'риба морожена'),
                ('Заморожені овочі', 'морква, броколі, кукурудза'),
                ('Пельмені', 'фарш (свинина), цибуля, тісто (борошно, вода)'),
                ('Котлети', 'м\'ясо, цибуля, хліб, спеції'),
                ('Заморожені фрукти', 'полуниця, малина, чорниця')
            ],
            'Зернові та бобові': [
                ('Гречка', 'ядриця гречана'),
                ('Перловка', 'перлова крупа'),
                ('Чорний рис', 'дикий чорний рис'),
                ('Квасоля', 'біла квасоля'),
                ('Боби', 'червоні боби')
            ],
            'Овочі та фрукти': [
                ('Яблука', 'яблука свіжі'),
                ('Банани', 'банани жовті'),
                ('Морква', 'морква очищена'),
                ('Картопля', 'картопля молода'),
                ('Помідори', 'помідори червоні')
            ],
            'Спеції та приправи': [
                ('Сіль', 'натуральна кам\'яна сіль'),
                ('Перець', 'мелений чорний перець'),
                ('Часник', 'сушений часник'),
                ('Імбир', 'мелений імбир'),
                ('Куркума', 'порошок куркуми')
            ]
        }

        # Створення категорій
        categories = []
        for i, (category_name, characteristics) in enumerate(product_categories[:n_categories]):
            category_number = i + 1
            db.session.execute(text("""
                INSERT INTO category (category_number, name) VALUES (:category_number, :name)
            """), {
                "category_number": category_number,
                "name": category_name
            })
            categories.append((category_number, category_name, characteristics))

        # Додавання працівників
        employee_id = 101
        cashier_ids = []
        for _ in range(n_employees):
            gender = choice(['male', 'female'])
            first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
            last_name = choice(last_names)
            middle_name = choice(middle_name_male) if gender == 'male' else choice(middle_name_female)
            position = choice(['Касир', 'Менеджер'])
            salary = round(uniform(12000, 25000), 2)
            start_date = fake.date_between(start_date='-5y', end_date='-1y')
            birth_date = fake.date_between(start_date='-50y', end_date='-20y')
            phone = generate_ua_phone()
            city = fake.city()
            street = fake.street_name()
            postal_code = fake.postcode()
            email = generate_email(first_name, last_name)
            password = generate_password_hash(generate_unique_password(first_name, last_name, birth_date.year))

            db.session.execute(text("""
                INSERT INTO employee (id, last_name, first_name, middle_name, position, salary, start_date, birth_date, 
                                     phone, city, street, postal_code, password, email)
                VALUES (:id, :last_name, :first_name, :middle_name, :position, :salary, :start_date, :birth_date, 
                       :phone, :city, :street, :postal_code, :password, :email)
            """), {
                "id": employee_id,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "position": position,
                "salary": salary,
                "start_date": start_date,
                "birth_date": birth_date,
                "phone": phone,
                "city": city,
                "street": street,
                "postal_code": postal_code,
                "password": password,
                "email": email
            })

            if position == 'Касир':
                cashier_ids.append(employee_id)

            employee_id += 1

        # Створення товарів
        product_id = 1001
        products = []
        for _ in range(n_products):
            category_number, category_name, characteristics = choice(categories)

            name_and_ingredient = choice(product_examples[category_name])
            product_name = name_and_ingredient[0]
            base_ingredient = name_and_ingredient[1]

            manufacturer = choice(manufacturer_examples[category_name])

            specs = {}
            for ch in characteristics:
                if ch == 'склад':
                    specs[ch] = base_ingredient
                else:
                    specs[ch] = generate_characteristic_value(ch)

            specifications = json.dumps(specs, ensure_ascii=False)

            db.session.execute(text("""
                INSERT INTO product (id, name, manufacturer, specifications, category_number)
                VALUES (:id, :name, :manufacturer, :specifications, :category_number)
            """), {
                "id": product_id,
                "name": product_name,
                "manufacturer": manufacturer,
                "specifications": specifications,
                "category_number": category_number
            })

            products.append(product_id)
            product_id += 1

        # Товари у магазині
        store_products = []
        for prod_id in products:
            upc = fake.unique.ean(length=13)
            price = round(uniform(50, 5000), 2)
            quantity = randint(1, 50)
            expiration_date = generate_expiration_date()

            # Визначення, чи є товар акційним і розрахунок акційної ціни
            soon_expiring = expiration_date <= datetime.now().date() + timedelta(days=7)
            high_quantity = quantity > 30
            is_promotional = soon_expiring and high_quantity
            promo_price = round(price * 0.8, 2) if is_promotional else price

            db.session.execute(text("""
                INSERT INTO store_product (upc, price, quantity, expiration_date, is_promotional, promo_price, product_id)
                VALUES (:upc, :price, :quantity, :expiration_date, :is_promotional, :promo_price, :product_id)
            """), {
                "upc": upc,
                "price": price,
                "quantity": quantity,
                "expiration_date": expiration_date,
                "is_promotional": is_promotional,
                "promo_price": promo_price,
                "product_id": prod_id
            })

            store_products.append(upc)

        # Клієнтські картки
        customer_cards = []
        for _ in range(n_customers):
            gender = choice(['male', 'female'])
            first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
            last_name = choice(last_names)
            middle_name = choice(middle_name_male) if gender == 'male' else choice(middle_name_female)
            card_number = fake.unique.bothify(text='####-####')
            phone = generate_ua_phone()
            city = fake.city()
            street = fake.street_name()
            postal_code = fake.postcode()
            discount_percent = round(uniform(0, 10), 2)

            db.session.execute(text("""
                INSERT INTO customer_card (card_number, last_name, first_name, middle_name, phone, city, street, 
                                         postal_code, discount_percent)
                VALUES (:card_number, :last_name, :first_name, :middle_name, :phone, :city, :street, 
                       :postal_code, :discount_percent)
            """), {
                "card_number": card_number,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "phone": phone,
                "city": city,
                "street": street,
                "postal_code": postal_code,
                "discount_percent": discount_percent
            })

            customer_cards.append(card_number)

        # Чеки - перевірка наявності касирів і створення чеків
        receipt_item_id = 2001

        # Ensure at least one cashier exists
        if not cashier_ids:
            print("Немає касирів для створення чеків!")
            # Create at least one cashier
            gender = choice(['male', 'female'])
            first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
            last_name = choice(last_names)
            middle_name = choice(middle_name_male) if gender == 'male' else choice(middle_name_female)
            position = 'Касир'  # Force this to be a cashier
            salary = round(uniform(12000, 25000), 2)
            start_date = fake.date_between(start_date='-5y', end_date='-1y')
            birth_date = fake.date_between(start_date='-50y', end_date='-20y')
            phone = generate_ua_phone()
            city = fake.city()
            street = fake.street_name()
            postal_code = fake.postcode()
            email = generate_email(first_name, last_name)
            password = generate_password_hash(generate_unique_password(first_name, last_name, birth_date.year))

            cashier_id = employee_id

            db.session.execute(text("""
                INSERT INTO employee (id, last_name, first_name, middle_name, position, salary, start_date, birth_date, 
                                    phone, city, street, postal_code, password, email)
                VALUES (:id, :last_name, :first_name, :middle_name, :position, :salary, :start_date, :birth_date, 
                      :phone, :city, :street, :postal_code, :password, :email)
            """), {
                "id": cashier_id,
                "last_name": last_name,
                "first_name": first_name,
                "middle_name": middle_name,
                "position": position,
                "salary": salary,
                "start_date": start_date,
                "birth_date": birth_date,
                "phone": phone,
                "city": city,
                "street": street,
                "postal_code": postal_code,
                "password": password,
                "email": email
            })

            cashier_ids.append(cashier_id)
            print(f"Створено касира з ID {cashier_id} для чеків")

            employee_id += 1

        for _ in range(n_receipts):
            receipt_number = fake.unique.bothify(text='R####')
            date = fake.date_time_between(start_date='-3y', end_date='now')
            customer_card_number = choice(customer_cards) if customer_cards else None
            employee_id = choice(cashier_ids)

            db.session.execute(text("""
                INSERT INTO receipt (receipt_number, date, customer_card_number, employee_id)
                VALUES (:receipt_number, :date, :customer_card_number, :employee_id)
            """), {
                "receipt_number": receipt_number,
                "date": date,
                "customer_card_number": customer_card_number,
                "employee_id": employee_id
            })

            # Позиції чеку
            items_count = randint(1, 5)
            for _ in range(items_count):
                upc = choice(store_products)
                quantity = randint(1, 5)

                db.session.execute(text("""
                    INSERT INTO receipt_item (id, receipt_number, upc, quantity)
                    VALUES (:id, :receipt_number, :upc, :quantity)
                """), {
                    "id": receipt_item_id,
                    "receipt_number": receipt_number,
                    "upc": upc,
                    "quantity": quantity
                })

                receipt_item_id += 1

        db.session.commit()
        print("База даних успішно заповнена!")


if __name__ == '__main__':
    seed_database()
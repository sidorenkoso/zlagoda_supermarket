from zlg_website import create_app, db  # Імпортуємо додаток і базу даних з вашого додатку
from zlg_website.models import Employee, Category, Product, StoreProduct, CustomerCard, Receipt, ReceiptItem
from faker import Faker
from random import randint, uniform, choice
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json
from sqlalchemy import text
import transliterate
from datetime import datetime
import random

fake = Faker('uk_UA')

# Створюємо додаток
app = create_app()
"""
generate_unique_password: Функція створює пароль, який містить перші 3 літери імені та прізвища працівника, а також рік народження.
Наприклад, якщо працівник має ім’я "Олександр", прізвище "Іванов", а рік народження 1990, то його пароль буде: олеіван1990. 
"""


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

def generate_unique_password(employee: Employee) -> str:
    first = transliterate.translit(employee.first_name[:3], reversed=True).lower()
    last = transliterate.translit(employee.last_name[:3], reversed=True).lower()
    return f"{first}{last}{employee.birth_date.year}"

def generate_email(employee) -> str:
    # Транслітерація імені та прізвища в латинку
    first = transliterate.translit(employee.first_name, 'uk', reversed=True).lower()
    last = transliterate.translit(employee.last_name, 'uk', reversed=True).lower()

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
        db.drop_all()  # Видаляємо таблиці (якщо вони існують)
        db.create_all()  # Створюємо таблиці (якщо ще не створені)

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

        # Працівники
        employee_id = 101
        employees = []
        for _ in range(n_employees):
            gender = choice(['male', 'female'])
            first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
            middle_name = choice(middle_name_male) if gender == 'male' else choice(middle_name_female)
            emp = Employee(
                id = employee_id,
                last_name=choice(last_names),
                first_name=first_name,
                middle_name=middle_name,
                position=choice(['Касир', 'Менеджер']),
                salary=round(uniform(12000, 25000), 2),
                start_date=fake.date_between(start_date='-5y', end_date='-1y'),
                birth_date=fake.date_between(start_date='-50y', end_date='-20y'),
                phone=generate_ua_phone(),
                city=fake.city(),
                street=fake.street_name(),
                postal_code=fake.postcode()
            )
            employee_id+=1
            emp.email = generate_email(emp)
            emp.password = generate_password_hash(generate_unique_password(emp))
            db.session.add(emp)
            employees.append(emp)

        # Категорії товарів із характеристиками
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
            'Продукти харчування': ['Хлібозавод', 'Галичина', 'Рудь', 'АВК', 'Слов’яночка'],
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
        for i, (category_name, characteristics) in enumerate(product_categories):
            cat = Category(category_number=i + 1, name=category_name)
            db.session.add(cat)
            categories.append((cat, characteristics))

        # Створення товарів
        product_id = 1001
        products = []
        for _ in range(n_products):
            category, characteristics = choice(categories)
            category_name = category.name

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

            product = Product(
                id = product_id,
                name=product_name,
                manufacturer=manufacturer,
                specifications=json.dumps(specs, ensure_ascii=False),
                category=category
            )
            product_id+=1
            db.session.add(product)
            products.append(product)

        # Товари у магазині
        store_products = []
        for prod in products:
            sp = StoreProduct(
                upc=fake.unique.ean(length=13),
                price=round(uniform(50, 5000), 2),
                quantity=randint(1, 50),
                expiration_date=generate_expiration_date(),
                product=prod
            )
            sp.is_promotional = sp.calculate_promotional
            sp.promo_price = sp.calculate_promo_price
            db.session.add(sp)
            store_products.append(sp)

        # Клієнтські картки
        customers = []
        for _ in range(n_customers):
            gender = choice(['male', 'female'])
            first_name = fake.first_name_male() if gender == 'male' else fake.first_name_female()
            middle_name = choice(middle_name_male) if gender == 'male' else choice(middle_name_female)
            card = CustomerCard(
                card_number=fake.unique.bothify(text='####-####'),
                last_name=choice(last_names),
                first_name=first_name,
                middle_name=middle_name,
                phone=generate_ua_phone(),
                city=fake.city(),
                street=fake.street_name(),
                postal_code=fake.postcode(),
                discount_percent=round(uniform(0, 10), 2)
            )
            db.session.add(card)
            customers.append(card)

        # Чеки
        receipt_item_id = 2001
        cashiers = [emp for emp in employees if emp.position == 'Касир']
        for _ in range(n_receipts):
            receipt = Receipt(
                receipt_number=fake.unique.bothify(text='R####'),
                date=fake.date_time_between(start_date='-3y', end_date='now'),
                customer_card=choice(customers),
                employee=choice(cashiers)
            )
            db.session.add(receipt)

            # Позиції чеку
            items_count = randint(1, 5)
            for _ in range(items_count):
                item = ReceiptItem(
                    id = receipt_item_id,
                    receipt=receipt,
                    store_product=choice(store_products),
                    quantity=randint(1, 5)
                )
                db.session.add(item)
                receipt_item_id += 1


        db.session.commit()

if __name__ == '__main__':
    seed_database()

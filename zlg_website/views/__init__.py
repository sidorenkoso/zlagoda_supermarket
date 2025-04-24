from flask import Blueprint

views = Blueprint("views", __name__)

# імпортуємо окремі частини (маршрути)
from . import (employees, home_welcome, add_employee, delete_employee, edit_employee, auth,
               clients, add_client, delete_client, edit_client, category, add_category, print_categories_report,
               edit_category, delete_category, products, add_product, edit_products, delete_products, storeproducts, add_storeproduct, delete_storeproduct, edit_storeproduct)
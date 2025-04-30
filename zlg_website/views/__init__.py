from flask import Blueprint

views = Blueprint("views", __name__)

# імпортуємо окремі частини (маршрути)
from . import (employees, home_welcome, auth, clients,category, print_report, products, storeproducts, receipts)
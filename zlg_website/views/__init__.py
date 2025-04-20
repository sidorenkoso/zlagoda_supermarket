from flask import Blueprint

views = Blueprint("views", __name__)

# імпортуємо окремі частини (маршрути)
from . import employees, home_welcome, add_employee, delete_employee, edit_employee, auth, clients, add_client, delete_client, edit_client, category, add_category
from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from zlg_website.models import db
from datetime import datetime
from . import views
from sqlalchemy import text


@views.route('/employees')
@login_required
def employees():
   if current_user.position != 'Менеджер':
       abort(403)


   search_query = request.args.get('search', '')
   position_filter = request.args.get('position')
   sort = request.args.get('sort')
   order = request.args.get('order', 'asc')


   query = "SELECT* FROM employee"
   filters = []
   params = {}


   if position_filter:
       filters.append("position = :position")
       params["position"] = position_filter


   if filters:
       query += " WHERE " + " AND ".join(filters)


   if sort == 'last_name':
       query += f" ORDER BY last_name {'DESC' if order == 'desc' else 'ASC'}"
   else:
       query += " ORDER BY id ASC"


   with db.engine.connect() as conn:
       result = conn.execute(text(query), params)
       employees = [dict(row._mapping) for row in result]


   if search_query:
       search_lower = search_query.lower()
       employees = [
           emp for emp in employees
           if emp.get('last_name') and emp['last_name'].lower().startswith(search_lower)
       ]


   for emp in employees:
       emp['full_name'] = f"{emp['last_name']} {emp['first_name']} {emp['middle_name']}".strip()
       emp['address'] = f"{emp['city']}, {emp['street']}, {emp['postal_code']}".strip()


   return render_template("employees.html", user=current_user, employees=employees, current_filter=position_filter)






@views.route('/employees/add', methods=['GET'])
@login_required
def add_employee_form():
   if current_user.position != 'Менеджер':
       abort(403)


   try:
       result = db.session.execute(text("SELECT id FROM employee ORDER BY id DESC LIMIT 1"))
       last_employee = result.fetchone()
       next_id = last_employee.id + 1 if last_employee else 1
   except Exception:
       next_id = 1


   return render_template("form_employees.html", user=current_user, next_id=next_id)




@views.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
   if current_user.position != 'Менеджер':
       abort(403)


   try:
       id = int(request.form.get("id"))
       full_name = request.form.get("full_name")
       position = request.form.get("position")
       salary = float(request.form.get("salary"))
       birth_date = datetime.strptime(request.form.get("birth_date"), "%Y-%m-%d").date()
       today = datetime.today()
       age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


       if age < 18:
           flash("Працівнику має бути не менше 18 років!", "error")
           return redirect(url_for("views.add_employee_form"))


       start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
       phone = request.form.get("phone")
       address = request.form.get("address")
       email = request.form.get("email")
       password = generate_password_hash(request.form.get("password"))


       parts = full_name.split(maxsplit=2)
       last_name = parts[0]
       first_name = parts[1] if len(parts) > 1 else ""
       middle_name = parts[2] if len(parts) > 2 else ""


       address_parts = [p.strip() for p in address.split(',')]
       if len(address_parts) != 3:
           raise ValueError("Адреса має бути в форматі: 'Місто, вулиця, поштовий індекс'")
       city, street, postal_code = address_parts


       insert_query = text("""
           INSERT INTO employee (
               id, last_name, first_name, middle_name, position, salary,
               birth_date, start_date, phone, city, street, postal_code,
               email, password
           ) VALUES (
               :id, :last_name, :first_name, :middle_name, :position, :salary,
               :birth_date, :start_date, :phone, :city, :street, :postal_code,
               :email, :password
           )
       """)


       db.session.execute(insert_query, {
           "id": id,
           "last_name": last_name,
           "first_name": first_name,
           "middle_name": middle_name,
           "position": position,
           "salary": salary,
           "birth_date": birth_date,
           "start_date": start_date,
           "phone": phone,
           "city": city,
           "street": street,
           "postal_code": postal_code,
           "email": email,
           "password": password
       })
       db.session.commit()


       flash("Працівника успішно додано!", "success")
       return redirect(url_for("views.employees"))


   except Exception as e:
       db.session.rollback()
       flash(f"Помилка при додаванні працівника: {str(e)}", "error")
       return redirect(url_for("views.add_employee_form"))




@views.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
   if current_user.position != 'Менеджер':
       abort(403)


   conn = db.engine.connect()


   if request.method == 'POST':
       try:
           full_name = request.form.get("full_name")
           position = request.form.get("position")
           salary = float(request.form.get("salary"))
           birth_date = datetime.strptime(request.form.get("birth_date"), "%Y-%m-%d").date()
           start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
           phone = request.form.get("phone")
           address = request.form.get("address")
           email = request.form.get("email")
           new_password = request.form.get("password")


           # Розділяємо повне ім'я
           parts = full_name.split(maxsplit=2)
           last_name = parts[0]
           first_name = parts[1] if len(parts) > 1 else ""
           middle_name = parts[2] if len(parts) > 2 else ""


           # Розділяємо адресу
           city, street, postal_code = [p.strip() for p in address.split(",")]


           # SQL оновлення
           if new_password:
               password = generate_password_hash(new_password)
               conn.execute(text("""
                   UPDATE employee SET
                       last_name = :last_name,
                       first_name = :first_name,
                       middle_name = :middle_name,
                       position = :position,
                       salary = :salary,
                       birth_date = :birth_date,
                       start_date = :start_date,
                       phone = :phone,
                       city = :city,
                       street = :street,
                       postal_code = :postal_code,
                       email = :email,
                       password = :password
                   WHERE id = :id
               """), {
                   "id": id, "last_name": last_name, "first_name": first_name, "middle_name": middle_name,
                   "position": position, "salary": salary, "birth_date": birth_date, "start_date": start_date,
                   "phone": phone, "city": city, "street": street, "postal_code": postal_code,
                   "email": email, "password": password
               })
           else:
               conn.execute(text("""
                   UPDATE employee SET
                       last_name = :last_name,
                       first_name = :first_name,
                       middle_name = :middle_name,
                       position = :position,
                       salary = :salary,
                       birth_date = :birth_date,
                       start_date = :start_date,
                       phone = :phone,
                       city = :city,
                       street = :street,
                       postal_code = :postal_code,
                       email = :email
                   WHERE id = :id
               """), {
                   "id": id, "last_name": last_name, "first_name": first_name, "middle_name": middle_name,
                   "position": position, "salary": salary, "birth_date": birth_date, "start_date": start_date,
                   "phone": phone, "city": city, "street": street, "postal_code": postal_code,
                   "email": email
               })


           conn.commit()
           flash("Зміни збережено успішно!", "success")
           return redirect(url_for('views.employees'))


       except Exception as e:
           conn.rollback()
           flash(f"Помилка при оновленні: {str(e)}", "error")
           return redirect(url_for('views.edit_employee', id=id))


   result = conn.execute(text("SELECT * FROM employee WHERE id = :id"), {"id": id})
   row = result.mappings().fetchone()
   if not row:
       abort(404)


   employee = dict(row)  # ← робимо звичайний словник


   # Приводимо дати до datetime.date
   employee['birth_date'] = datetime.strptime(employee['birth_date'], '%Y-%m-%d').date()
   employee['start_date'] = datetime.strptime(employee['start_date'], '%Y-%m-%d').date()


   # Створюємо повне ім’я та адресу (якщо потрібно для шаблону)
   employee['full_name'] = f"{employee['last_name']} {employee['first_name']} {employee['middle_name']}".strip()
   employee['address'] = f"{employee['city']}, {employee['street']}, {employee['postal_code']}".strip()


   return render_template("form_employees.html", user=current_user, employee=employee)




@views.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
   if current_user.position != 'Менеджер':
       abort(403)


   try:
       db.session.execute(text("DELETE FROM employee WHERE id = :id"), {"id": id})
       db.session.commit()
       flash("Працівника успішно видалено!", "success")
   except Exception as e:
       db.session.rollback()
       flash(f"Помилка при видаленні: {str(e)}", "error")


   return redirect(url_for("views.employees"))
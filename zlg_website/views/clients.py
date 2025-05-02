from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from sqlalchemy import text
from zlg_website.models import db
from . import views
import random


@views.route('/clients')
@login_required
def clients():
   search_query = request.args.get('search', '')
   city_filter = request.args.get('city')
   sort = request.args.get('sort')
   order = request.args.get('order', 'asc')


   base_query = "SELECT * FROM customer_card"
   filters = []
   params = {}


   if city_filter:
       filters.append("city ILIKE :city")
       params['city'] = f"%{city_filter}%"


   if filters:
       base_query += " WHERE " + " AND ".join(filters)


   if sort == 'last_name':
       base_query += f" ORDER BY last_name {'DESC' if order == 'desc' else 'ASC'}"
   else:
       base_query += " ORDER BY card_number ASC"


   result = db.session.execute(text(base_query), params)
   clients = [dict(row._mapping) for row in result.fetchall()]




   if search_query:
       if current_user.position == 'Менеджер':
           try:
               discount_value = int(float(search_query))
               clients = [c for c in clients if discount_value <= c['discount_percent'] < discount_value + 1]
           except ValueError:
               clients = []
       elif current_user.position == 'Касир':
           lowered = search_query.lower()
           clients = [c for c in clients if c['last_name'] and c['last_name'].lower().startswith(lowered)]


   return render_template("clients.html", user=current_user, clients=clients,
                          current_city=city_filter, search_query=search_query)




@views.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
   result = db.session.execute(text("SELECT card_number FROM customer_card"))
   existing_numbers = {dict(row._mapping)['card_number'] for row in result.fetchall()}




   while True:
       prefix = str(random.randint(1000, 9999))
       suffix = str(random.randint(1000, 9999))
       card_number = f"{prefix}-{suffix}"
       if card_number not in existing_numbers:
           break


   if request.method == "POST":
       try:
           last_name = request.form.get("last_name")
           first_name = request.form.get("first_name")
           middle_name = request.form.get("middle_name")
           phone = request.form.get("phone")
           city = request.form.get("city") or None
           street = request.form.get("street") or None
           postal_code = request.form.get("postal_code") or None
           discount_percent = float(request.form.get("discount_percent"))


           insert_query = text("""
               INSERT INTO customer_card (
                   card_number, last_name, first_name, middle_name, phone, city, street, postal_code, discount_percent
               ) VALUES (
                   :card_number, :last_name, :first_name, :middle_name, :phone, :city, :street, :postal_code, :discount_percent
               )
           """)


           db.session.execute(insert_query, {
               'card_number': card_number,
               'last_name': last_name,
               'first_name': first_name,
               'middle_name': middle_name,
               'phone': phone,
               'city': city,
               'street': street,
               'postal_code': postal_code,
               'discount_percent': discount_percent
           })
           db.session.commit()


           flash("Клієнта успішно додано!", "success")
           return redirect(url_for("views.clients"))


       except Exception as e:
           db.session.rollback()
           flash(f"Помилка при додаванні клієнта: {str(e)}", "error")
           return redirect(url_for("views.add_client"))


   return render_template("form_clients.html", mode="add", card_number=card_number, user=current_user)




@views.route('/clients/edit/<string:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
   result = db.session.execute(text("SELECT * FROM customer_card WHERE card_number = :id"), {'id': client_id})
   row = result.fetchone()
   if row is None:
       abort(404)
   client = dict(row._mapping)


   if request.method == 'POST':
       try:
           update_query = text("""
               UPDATE customer_card SET
                   last_name = :last_name,
                   first_name = :first_name,
                   middle_name = :middle_name,
                   phone = :phone,
                   city = :city,
                   street = :street,
                   postal_code = :postal_code,
                   discount_percent = :discount_percent
               WHERE card_number = :card_number
           """)


           db.session.execute(update_query, {
               'last_name': request.form['last_name'],
               'first_name': request.form['first_name'],
               'middle_name': request.form.get('middle_name', ''),
               'phone': request.form['phone'],
               'city': request.form['city'],
               'street': request.form['street'],
               'postal_code': request.form['postal_code'],
               'discount_percent': float(request.form['discount_percent']),
               'card_number': client_id
           })
           db.session.commit()


           flash("Картку клієнта успішно оновлено!", category='success')
           return redirect(url_for('views.clients'))


       except Exception as e:
           db.session.rollback()
           flash(f"Помилка при оновленні: {str(e)}", "error")
           return redirect(url_for('views.edit_client', client_id=client_id))


   return render_template("form_clients.html", mode="edit", user=current_user, client=client)




@views.route('/clients/delete/<string:card_number>', methods=['POST'])
@login_required
def delete_client(card_number):
   db.session.execute(text("DELETE FROM customer_card WHERE card_number = :card_number"), {"card_number": card_number})
   db.session.commit()
   flash("Клієнта успішно видалено", "success")
   return redirect(url_for('views.clients'))
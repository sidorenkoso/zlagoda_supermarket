from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import CustomerCard, db
from datetime import datetime
from sqlalchemy import func
from . import views
import random

@views.route('/clients')
@login_required
def clients():
    search_query = request.args.get('search', '')
    city_filter = request.args.get('city')
    sort = request.args.get('sort')
    order = request.args.get('order', 'asc')

    query = CustomerCard.query

    if city_filter:
        query = query.filter(CustomerCard.city.ilike(f"%{city_filter}%"))


    # Сортування
    if sort == 'last_name':
        query = query.order_by(
            CustomerCard.last_name.desc() if order == 'desc' else CustomerCard.last_name.asc()
        )
    else:
        query = query.order_by(CustomerCard.card_number.asc())

    clients = query.all()

    if search_query:
        if search_query:
            if current_user.position == 'Менеджер':
                try:
                    discount_value = int(float(search_query))
                    clients = [c for c in clients if discount_value <= c.discount_percent < discount_value + 1]
                except ValueError:
                    clients = []
            elif current_user.position == 'Касир':
                lowered = search_query.lower()
                clients = [c for c in clients if lowered in c.last_name.lower()]

    return render_template("clients.html", user=current_user, clients=clients,
                           current_city=city_filter, search_query=search_query)


@views.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():

    # Генеруємо унікальний номер — і для GET, і для POST
    existing_numbers = {c.card_number for c in CustomerCard.query.all()}

    while True:
        prefix = str(random.randint(1000, 9999))
        suffix = str(random.randint(1000, 9999))
        card_number = f"{prefix}-{suffix}"
        if card_number not in existing_numbers:
            break

    if request.method == "POST":
        try:
            # Використовуємо card_number, згенерований вище
            last_name = request.form.get("last_name")
            first_name = request.form.get("first_name")
            middle_name = request.form.get("middle_name")
            phone = request.form.get("phone")
            city = request.form.get("city") or None
            street = request.form.get("street") or None
            postal_code = request.form.get("postal_code") or None
            discount_percent = float(request.form.get("discount_percent"))

            new_client = CustomerCard(
                card_number=card_number,
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                phone=phone,
                city=city,
                street=street,
                postal_code=postal_code,
                discount_percent=discount_percent
            )

            db.session.add(new_client)
            db.session.commit()

            flash("Клієнта успішно додано!", "success")
            return redirect(url_for("views.clients"))

        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при додаванні клієнта: {str(e)}", "error")
            return redirect(url_for("views.add_client"))

    # GET — просто показати форму з уже згенерованим card_number
    return render_template("form_clients.html", mode="add", card_number=card_number, user=current_user)


@views.route('/clients/edit/<string:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):

    client = CustomerCard.query.get_or_404(client_id)

    if request.method == 'POST':
        try:
            client.last_name = request.form['last_name']
            client.first_name = request.form['first_name']
            client.middle_name = request.form.get('middle_name', '')
            client.phone = request.form['phone']
            client.city = request.form['city']
            client.street = request.form['street']
            client.postal_code = request.form['postal_code']
            client.discount_percent = float(request.form['discount_percent'])

            db.session.commit()
            flash("Картку клієнта успішно оновлено!", category='success')
            return redirect(url_for('views.clients'))

        except Exception as e:
            db.session.rollback()
            flash(f"Помилка при оновленні: {str(e)}", "error")
            return redirect(url_for('views.edit_client', client_id=client.id))

    return render_template("form_clients.html", mode="edit", user=current_user, client=client)


@views.route('/clients/delete/<string:card_number>', methods=['POST'])
@login_required
def delete_client(card_number):
    client = CustomerCard.query.get_or_404(card_number)
    db.session.delete(client)
    db.session.commit()
    flash("Клієнта успішно видалено", "success")
    return redirect(url_for('views.clients'))

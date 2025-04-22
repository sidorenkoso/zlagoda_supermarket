from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import CustomerCard, db
from . import views
import random

@views.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    if current_user.position != 'Менеджер':
        abort(403)

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
    return render_template("add_cards.html", card_number=card_number, user=current_user)

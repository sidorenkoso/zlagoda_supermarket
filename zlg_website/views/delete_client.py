from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import CustomerCard, db
from . import views

@views.route('/clients/delete/<string:card_number>', methods=['POST'])
@login_required
def delete_client(card_number):
    client = CustomerCard.query.get_or_404(card_number)
    db.session.delete(client)
    db.session.commit()
    flash("Клієнта успішно видалено", "success")
    return redirect(url_for('views.clients'))

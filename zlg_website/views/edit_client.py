from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from zlg_website.models import CustomerCard, db
from . import views  # існуючий Blueprint

@views.route('/clients/edit/<string:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    if current_user.position != 'Менеджер':
        abort(403)

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
            return redirect(url_for('views.edit_client', id=id))

    return render_template("edit_cards.html", user=current_user, client=client)

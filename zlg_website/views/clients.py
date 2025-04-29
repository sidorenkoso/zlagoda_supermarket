from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import CustomerCard, db
from datetime import datetime
from sqlalchemy import func
from . import views

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
        search_lower = search_query.lower()
        clients = [
            cli for cli in clients
            if search_lower in cli.last_name.lower()
        ]

    return render_template("clients.html", user=current_user, clients=clients,
                           current_city=city_filter, search_query=search_query)

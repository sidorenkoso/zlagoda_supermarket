from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from zlg_website.models import Category, db
from . import views

@views.route('/categories/report')
@login_required
def print_categories_report():
    if current_user.position != 'Менеджер':
        abort(403)

    flash("Звіт по категоріях сформовано", 'success')
    return redirect(url_for('views.categories'))
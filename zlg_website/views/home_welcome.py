from flask import render_template
from flask_login import login_required, current_user
from . import views

@views.route('/')
@login_required
def home():
    # Відображати сторінку головна (main.html)
    return render_template("main.html", user=current_user)


@views.route('/welcome')
@login_required
def welcome():
    # Відображати сторінку привітання (home.html)
    return render_template("home.html", user=current_user)
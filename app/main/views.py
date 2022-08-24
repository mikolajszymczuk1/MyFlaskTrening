from datetime import datetime
from flask import render_template
from . import main
from .forms import NameForm
from .. import db
from ..models import User
from ..email import send_email


# Index endpoint
@main.route('/', methods=['GET', 'POST'])
def index():
    all_users = User.query.all()
    return render_template('index.html', users=all_users)


# User endpoint
@main.get('/user/<string:username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)

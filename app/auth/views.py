from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm
from .. import db


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if (next is None or not next.startswith('/')):
                next = url_for('main.index')

            return redirect(next)
        flash('Invalid username or password !')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out !')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)  # type: ignore

        db.session.add(user)
        db.session.commit()
        flash('You can login now !')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth.get('/secret')
@login_required
def secret():
    return '<h1>Secret page :)</h1>'

from flask import render_template, redirect, request, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ..models import User
from .forms import (
    LoginForm,
    RegistrationForm,
    ChangePasswordForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    ChangeEmailForm
)
from .. import db
from ..email import send_email


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


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
                    password=form.password.data)

        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm your account', 'auth/mail/confirm', user=user, token=token)
        flash('We have sent a message with an activation link to your e-mail address')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth.get('/secret')
@login_required
def secret():
    return '<h1>Secret page :)</h1>'


@auth.get('/confirm/<string:token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))

    if current_user.confirm(token):
        db.session.commit()
        flash('You confirmed your account, thank you !')
    else:
        flash('Activation link is invalid')

    return redirect(url_for('main.index'))


@auth.get('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))

    return render_template('auth/unconfirmed.html')


@auth.get('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'A new confirmation message has been sent',
        'auth/mail/confirm', user=current_user, token=token)

    flash('A new confirmation message has been sent')
    return redirect(url_for('main.index'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.new_password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been changed')
        else:
            flash('Old password is wrong')
            return redirect(url_for('main.index'))


    return render_template('auth/changePassword.html', form=form)


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Reset password link', 'auth/mail/resetPassword', user=user, token=token)
        flash('We have sent a message with an link for reset your password to your e-mail address')
        session['userResetPasswordEmail'] = form.email.data
        return redirect(url_for('auth.login'))

    return render_template('auth/forgotPassword.html', form=form)


@auth.route('/reset-password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(email=session.get('userResetPasswordEmail')).first()
    if user.confirm(token):
        flash('You can now set new password for your account !')
    else:
        flash('Reset link is invalid')
        return redirect(url_for('main.index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.new_password.data
        db.session.add(user)
        db.session.commit()
        session.clear()
        return redirect(url_for('auth.login'))

    return render_template('auth/resetPassword.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = current_user.generate_change_email_token(form.new_email.data)
        send_email(current_user.email, 'Change email link', 'auth/mail/changeEmail', user=current_user, token=token)
        flash('We have sent a message with a link for confirm email change operation for your account')
        return redirect(url_for('main.index'))

    return render_template('auth/changeEmail.html', form=form)


@auth.get('/confirm-change-email/<string:token>')
@login_required
def confirm_change_email(token):
    if current_user.confirm(token):
        db.session.commit()
        flash('Your email was changed !')
    else:
        flash('Change email link is invalid')

    return redirect(url_for('main.index'))

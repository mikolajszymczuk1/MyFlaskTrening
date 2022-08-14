from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[DataRequired(), Length(1, 64), Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
        'Username should contains only letters, numbers, dots and underscore chars')])

    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password_repeat',
        message='Both passwords must be identical')])

    password_repeat = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('This email already exists !')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('This username already exists !')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    new_password = PasswordField('New password', validators=[DataRequired(), EqualTo('repeat_password',
        message='Passwords must be the same !')])

    repeat_password = PasswordField('Repeat new password', validators=[DataRequired()])
    submit = SubmitField('Change')


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    submit = SubmitField('Send reset link')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('We can not find account with this email !')


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New password', validators=[DataRequired(), EqualTo('repeat_password',
        message='Passwords must be the same !')])
    repeat_password = PasswordField('Repeat new password', validators=[DataRequired()])
    submit = SubmitField('Reset password')

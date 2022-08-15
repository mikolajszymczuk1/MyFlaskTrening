from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager
from flask_login import UserMixin
from flask import current_app
from itsdangerous.url_safe import URLSafeSerializer


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self) -> str:
        return '<Role %r' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self) -> None:
        raise AttributeError('Can not read attribute password')

    @password.setter
    def password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return '<User %r' % self.username

    def generate_confirmation_token(self):
        s = URLSafeSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({ 'confirm': self.id })

    def generate_change_email_token(self, newEmail):
        s = URLSafeSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({ 'confirm': self.id, 'newEmail': newEmail })

    def confirm(self, token):
        s = URLSafeSerializer(current_app.config['SECRET_KEY'])

        try:
            data = s.loads(token)
        except:
            return False

        if data.get('confirm') != self.id:
            return False

        self.confirmed = True
        newEmail = data.get('newEmail')
        if newEmail and newEmail != '':
            self.email = data.get('newEmail')

        db.session.add(self)
        return True


@login_manager.user_loader
def load_user(user_id: int) -> User:
    return User.query.get(int(user_id))

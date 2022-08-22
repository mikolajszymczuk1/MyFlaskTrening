from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from . import login_manager
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app
from itsdangerous.url_safe import URLSafeSerializer


class Permissions:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permissions.FOLLOW, Permissions.COMMENT, Permissions.WRITE],
            'Moderator': [Permissions.FOLLOW, Permissions.COMMENT, Permissions.WRITE, Permissions.MODERATE],
            'Administrator': [Permissions.FOLLOW, Permissions.COMMENT, Permissions.WRITE, Permissions.MODERATE, Permissions.ADMIN]
        }

        default_role= 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def __repr__(self) -> str:
        return '<Role %r' % self.name

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['APP_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permissions.ADMIN)

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


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


login_manager.anonymous_user = AnonymousUser

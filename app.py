from enum import unique
from flask import Flask, redirect, session, url_for, render_template, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_migrate import Migrate
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from os import environ

# Flask config

MYSQL_URI = 'mysql://root:{}@localhost/testFlask'.format(environ.get('DATABASE_PASSWORD'))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask shell config

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)

# Models

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self) -> str:
        return '<Role %r' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def __repr__(self) -> str:
        return '<User %r' % self.username

# Simple form

class NameForm(FlaskForm):
    name = StringField('What is your name ?', validators=[DataRequired()])
    submit = SubmitField('Send')


# Controllers

# Index endpoint
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    all_users = User.query.all()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.name.data).first()
        if user is None:
            user = User(username=form.name.data)
            db.session.add(user)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True

        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('user', name=session.get('name')))

    return render_template('index.html',
        form=form, name=session.get('name'), known=session.get('known', False), users=all_users)

# User endpoint
@app.get('/user/<string:name>')
def user(name):
    return render_template('user.html', name=name)

# 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

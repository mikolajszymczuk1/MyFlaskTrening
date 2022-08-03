from flask import Flask, redirect, session, url_for, render_template, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_migrate import Migrate
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from os import environ
from threading import Thread

# Flask config

MYSQL_URI = 'mysql://root:{}@localhost/testFlask'.format(environ.get('DATABASE_PASSWORD'))

app = Flask(__name__)

# Database config
app.config['SECRET_KEY'] = 'some secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail config
app.config['MAIL_SERVER'] = 'smtp.wp.pl'
app.config['MAIL_PORT'] = '465'
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = environ.get('MAIL_PASSWORD')

# Mail utils

app.config['APP_MAIL_SUBJECT_PREFIX'] = '[App]'
app.config['APP_MAIL_SENDER'] = 'App Admin <fela55555@wp.pl>'
app.config['APP_ADMIN'] = environ.get('APP_ADMIN')

def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    """ Function to sending mails """

    msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + subject,
                  sender=app.config['APP_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr

# Packages init

Bootstrap(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

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

            if app.config['APP_ADMIN']:
                send_email(app.config['APP_ADMIN'], 'New User !', 'mail/new_user', user=user)
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

from flask import Flask, redirect, session, url_for, render_template, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'some secret key'
Bootstrap(app)

# Simple form

class NameForm(FlaskForm):
    name = StringField('What is your name ?', validators=[DataRequired()])
    submit = SubmitField('Send')

# Controllers

# Index endpoint
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Name was changed !')

        session['name'] = form.name.data
        return redirect(url_for('user', name=session.get('name')))

    return render_template('index.html', form=form, name=session.get('name'))

# User endpoint
@app.get('/user/<string:name>')
def user(name):
    return render_template('user.html', name=name)

# 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Filename: app.py
# Full path: app.py

# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SubmitField, SelectField, IntegerField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from datetime import datetime
import os
from sqlalchemy import func
import logging
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random string for security

# Use environment variable for DB URI (PostgreSQL on Render, fallback to SQLite)
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///milk_tracker.db')
if db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
app.logger.info(f"Using database URI: {db_uri}")

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Distribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    liters = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Cow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    milks = db.relationship('MilkProduction', backref='cow', lazy=True)
    feeds = db.relationship('Feed', backref='cow', lazy=True)

class MilkProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cow_id = db.Column(db.Integer, db.ForeignKey('cow.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    liters = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cow_id = db.Column(db.Integer, db.ForeignKey('cow.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class FamilyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    address = StringField('Address')
    submit = SubmitField('Add Family')

class DistributionForm(FlaskForm):
    family_id = SelectField('Family', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    liters = FloatField('Liters', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Log Distribution')

class PaymentForm(FlaskForm):
    family_id = SelectField('Family', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    amount_paid = FloatField('Amount Paid', validators=[DataRequired()])
    submit = SubmitField('Record Payment')

class ExpenseForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    category = SelectField('Category', choices=[('feed', 'Feed'), ('vet', 'Vet'), ('other', 'Other')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Log Expense')

class CowForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired()])
    submit = SubmitField('Add Cow')

class MilkForm(FlaskForm):
    cow_id = SelectField('Cow', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    liters = FloatField('Liters', validators=[DataRequired()])
    submit = SubmitField('Log Milk')

class FeedForm(FlaskForm):
    cow_id = SelectField('Cow', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    type = SelectField('Type', choices=[('grass', 'Grass'), ('concentrate', 'Concentrate'), ('silage', 'Silage')], validators=[DataRequired()])
    amount = FloatField('Amount (kg)', validators=[DataRequired()])
    submit = SubmitField('Log Feed')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Change Password')

# Routes
@app.route('/')
@app.route('/index')
@login_required
def index():
    families = Family.query.filter_by(user_id=current_user.id).all()
    total_milk = db.session.query(func.sum(MilkProduction.liters)).filter_by(user_id=current_user.id).scalar() or 0
    total_revenue = db.session.query(func.sum(Distribution.amount)).filter_by(user_id=current_user.id).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id).scalar() or 0
    profit = total_revenue - total_expenses
    return render_template('index.html', families=families, total_milk=total_milk, total_revenue=total_revenue, total_expenses=total_expenses, profit=profit)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_family', methods=['GET', 'POST'])
@login_required
def add_family():
    form = FamilyForm()
    if form.validate_on_submit():
        family = Family(name=form.name.data, address=form.address.data, user_id=current_user.id)
        db.session.add(family)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_family.html', form=form)

@app.route('/log_distribution', methods=['GET', 'POST'])
@login_required
def log_distribution():
    form = DistributionForm()
    form.family_id.choices = [(f.id, f.name) for f in Family.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        dist = Distribution(family_id=form.family_id.data, date=form.date.data, liters=form.liters.data, amount=form.amount.data, user_id=current_user.id)
        db.session.add(dist)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('log_distribution.html', form=form)

@app.route('/record_payment', methods=['GET', 'POST'])
@login_required
def record_payment():
    form = PaymentForm()
    form.family_id.choices = [(f.id, f.name) for f in Family.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        pay = Payment(family_id=form.family_id.data, date=form.date.data, amount_paid=form.amount_paid.data, user_id=current_user.id)
        db.session.add(pay)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('record_payment.html', form=form)

@app.route('/log_expense', methods=['GET', 'POST'])
@login_required
def log_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(date=form.date.data, category=form.category.data, amount=form.amount.data, description=form.description.data, user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('expenses'))
    return render_template('log_expense.html', form=form)

@app.route('/expenses')
@login_required
def expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    total_expenses = sum(e.amount for e in expenses)
    return render_template('expenses.html', expenses=expenses, total_expenses=total_expenses)

@app.route('/view_family/<int:family_id>')
@login_required
def view_family(family_id):
    family = Family.query.filter_by(id=family_id, user_id=current_user.id).first_or_404()
    distributions = Distribution.query.filter_by(family_id=family_id, user_id=current_user.id).order_by(Distribution.date.desc()).all()
    payments = Payment.query.filter_by(family_id=family_id, user_id=current_user.id).order_by(Payment.date.desc()).all()
    total_amount = sum(d.amount for d in distributions)
    total_paid = sum(p.amount_paid for p in payments)
    balance = total_amount - total_paid
    return render_template('view_family.html', family=family, distributions=distributions, payments=payments, balance=balance)

@app.route('/add_cow', methods=['GET', 'POST'])
@login_required
def add_cow():
    form = CowForm()
    if form.validate_on_submit():
        cow = Cow(name=form.name.data, age=form.age.data, user_id=current_user.id)
        db.session.add(cow)
        db.session.commit()
        return redirect(url_for('cows'))
    return render_template('add_cow.html', form=form)

@app.route('/log_milk', methods=['GET', 'POST'])
@login_required
def log_milk():
    form = MilkForm()
    form.cow_id.choices = [(c.id, c.name) for c in Cow.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        milk = MilkProduction(cow_id=form.cow_id.data, date=form.date.data, liters=form.liters.data, user_id=current_user.id)
        db.session.add(milk)
        db.session.commit()
        return redirect(url_for('cows'))
    return render_template('log_milk.html', form=form)

@app.route('/log_feed', methods=['GET', 'POST'])
@login_required
def log_feed():
    form = FeedForm()
    form.cow_id.choices = [(c.id, c.name) for c in Cow.query.filter_by(user_id=current_user.id).all()]
    if form.validate_on_submit():
        feed = Feed(cow_id=form.cow_id.data, date=form.date.data, amount=form.amount.data, type=form.type.data, user_id=current_user.id)
        db.session.add(feed)
        db.session.commit()
        return redirect(url_for('cows'))
    return render_template('log_feed.html', form=form)

@app.route('/cows')
@login_required
def cows():
    cows = Cow.query.filter_by(user_id=current_user.id).all()
    return render_template('cows.html', cows=cows)

@app.route('/meal_plan')
@login_required
def meal_plan():
    return render_template('meal_plan.html')

@app.route('/other')
@login_required
def other():
    return render_template('other.html')

@app.route('/notifications')
@login_required
def notifications():
    families = Family.query.filter_by(user_id=current_user.id).all()
    alerts = []
    for f in families:
        total_amount = db.session.query(func.sum(Distribution.amount)).filter_by(family_id=f.id).scalar() or 0
        total_paid = db.session.query(func.sum(Payment.amount_paid)).filter_by(family_id=f.id).scalar() or 0
        balance = total_amount - total_paid
        if balance > 0:
            alerts.append({'family': f, 'balance': balance})
    return render_template('notifications.html', alerts=alerts)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash('Password changed successfully.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', form=form)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
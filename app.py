# app.py
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired
from datetime import datetime
import os
from sqlalchemy import create_engine, inspect, func
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random string for security

# Use environment variable for DB URI (PostgreSQL on Render, fallback to SQLite)
db_uri = os.environ.get('DATABASE_URL', 'sqlite:///milk_tracker.db')
if db_uri.startswith('postgres://'):
    db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
app.logger.info(f"Using database URI: {db_uri}")

# Database Models
class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200))

class Distribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    liters = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))

class Cow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    milks = db.relationship('MilkProduction', backref='cow', lazy=True)
    feeds = db.relationship('Feed', backref='cow', lazy=True)

class MilkProduction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cow_id = db.Column(db.Integer, db.ForeignKey('cow.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    liters = db.Column(db.Float, nullable=False)

class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cow_id = db.Column(db.Integer, db.ForeignKey('cow.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50))

# Initialize database tables if they don't exist
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
required_tables = {'family', 'distribution', 'payment', 'expense', 'cow', 'milk_production', 'feed'}

if not all(table in existing_tables for table in required_tables):
    with app.app_context():
        db.create_all()
    app.logger.info("Created missing database tables.")
else:
    app.logger.info("All database tables already exist.")

# Forms
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
    category = SelectField('Category', choices=[('Feed', 'Feed'), ('Veterinary', 'Veterinary'), ('Maintenance', 'Maintenance'), ('Labor', 'Labor'), ('Other', 'Other')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField('Log Expense')

class CowForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    age = IntegerField('Age')
    submit = SubmitField('Add Cow')

class MilkForm(FlaskForm):
    cow_id = SelectField('Cow', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    liters = FloatField('Liters', validators=[DataRequired()])
    submit = SubmitField('Log Milk')

class FeedForm(FlaskForm):
    cow_id = SelectField('Cow', coerce=int, validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()], default=datetime.today)
    type = SelectField('Type', choices=[('Grass', 'Grass'), ('Hay', 'Hay'), ('Concentrate', 'Concentrate'), ('Silage', 'Silage'), ('Other', 'Other')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Log Feed')

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    families = Family.query.all()
    num_families = len(families)
    total_milk = db.session.query(func.sum(MilkProduction.liters)).scalar() or 0
    total_distributed = db.session.query(func.sum(Distribution.liters)).scalar() or 0
    total_payments = db.session.query(func.sum(Payment.amount_paid)).scalar() or 0
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0
    profit = total_payments - total_expenses
    return render_template('index.html', families=families, num_families=num_families, total_milk=total_milk, total_distributed=total_distributed, total_payments=total_payments, total_expenses=total_expenses, profit=profit)

@app.route('/add_family', methods=['GET', 'POST'])
def add_family():
    form = FamilyForm()
    if form.validate_on_submit():
        family = Family(name=form.name.data, address=form.address.data)
        db.session.add(family)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_family.html', form=form)

@app.route('/log_distribution', methods=['GET', 'POST'])
def log_distribution():
    form = DistributionForm()
    form.family_id.choices = [(f.id, f.name) for f in Family.query.all()]
    if form.validate_on_submit():
        dist = Distribution(family_id=form.family_id.data, date=form.date.data, liters=form.liters.data, amount=form.amount.data)
        db.session.add(dist)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('log_distribution.html', form=form)

@app.route('/record_payment', methods=['GET', 'POST'])
def record_payment():
    form = PaymentForm()
    form.family_id.choices = [(f.id, f.name) for f in Family.query.all()]
    if form.validate_on_submit():
        payment = Payment(family_id=form.family_id.data, date=form.date.data, amount_paid=form.amount_paid.data)
        db.session.add(payment)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('record_payment.html', form=form)

@app.route('/log_expense', methods=['GET', 'POST'])
def log_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(date=form.date.data, category=form.category.data, amount=form.amount.data, description=form.description.data)
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('expenses'))
    return render_template('log_expense.html', form=form)

@app.route('/expenses')
def expenses():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    total_expenses = sum(e.amount for e in expenses)
    return render_template('expenses.html', expenses=expenses, total_expenses=total_expenses)

@app.route('/view_family/<int:family_id>')
def view_family(family_id):
    family = Family.query.get_or_404(family_id)
    distributions = Distribution.query.filter_by(family_id=family_id).order_by(Distribution.date.desc()).all()
    payments = Payment.query.filter_by(family_id=family_id).order_by(Payment.date.desc()).all()
    total_amount = sum(d.amount for d in distributions)
    total_paid = sum(p.amount_paid for p in payments)
    balance = total_amount - total_paid
    return render_template('view_family.html', family=family, distributions=distributions, payments=payments, balance=balance)

@app.route('/add_cow', methods=['GET', 'POST'])
def add_cow():
    form = CowForm()
    if form.validate_on_submit():
        cow = Cow(name=form.name.data, age=form.age.data)
        db.session.add(cow)
        db.session.commit()
        return redirect(url_for('cows'))
    return render_template('add_cow.html', form=form)

@app.route('/log_milk', methods=['GET', 'POST'])
def log_milk():
    form = MilkForm()
    form.cow_id.choices = [(c.id, c.name) for c in Cow.query.all()]
    if form.validate_on_submit():
        milk = MilkProduction(cow_id=form.cow_id.data, date=form.date.data, liters=form.liters.data)
        db.session.add(milk)
        db.session.commit()
        return redirect(url_for('cows'))
    return render_template('log_milk.html', form=form)

@app.route('/log_feed', methods=['GET', 'POST'])
def log_feed():
    form = FeedForm()
    form.cow_id.choices = [(c.id, c.name) for c in Cow.query.all()]
    if form.validate_on_submit():
        feed = Feed(cow_id=form.cow_id.data, date=form.date.data, amount=form.amount.data, type=form.type.data)
        db.session.add(feed)
        db.session.commit()
        return redirect(url_for('cows'))
    return render_template('log_feed.html', form=form)

@app.route('/cows')
def cows():
    cows = Cow.query.all()
    return render_template('cows.html', cows=cows)

@app.route('/meal_plan')
def meal_plan():
    return render_template('meal_plan.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
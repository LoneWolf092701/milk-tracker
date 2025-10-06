from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random string for security
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///milk_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

# Forms
class FamilyForm(FlaskForm):
    name = StringField('Family Name', validators=[DataRequired()])
    address = StringField('Address')
    submit = SubmitField('Add Family')

class DistributionForm(FlaskForm):
    family_id = StringField('Family ID', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    liters = FloatField('Liters', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Log Distribution')

class PaymentForm(FlaskForm):
    family_id = StringField('Family ID', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    amount_paid = FloatField('Amount Paid', validators=[DataRequired()])
    submit = SubmitField('Record Payment')

# Routes
@app.route('/')
def index():
    families = Family.query.all()
    return render_template('index.html', families=families)

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
    if form.validate_on_submit():
        dist = Distribution(family_id=form.family_id.data, date=form.date.data, liters=form.liters.data, amount=form.amount.data)
        db.session.add(dist)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('log_distribution.html', form=form)

@app.route('/record_payment', methods=['GET', 'POST'])
def record_payment():
    form = PaymentForm()
    if form.validate_on_submit():
        payment = Payment(family_id=form.family_id.data, date=form.date.data, amount_paid=form.amount_paid.data)
        db.session.add(payment)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('record_payment.html', form=form)

@app.route('/view_family/<int:family_id>')
def view_family(family_id):
    family = Family.query.get_or_404(family_id)
    distributions = Distribution.query.filter_by(family_id=family_id).all()
    payments = Payment.query.filter_by(family_id=family_id).all()
    total_amount = sum(d.amount for d in distributions)
    total_paid = sum(p.amount_paid for p in payments)
    balance = total_amount - total_paid
    return render_template('view_family.html', family=family, distributions=distributions, payments=payments, balance=balance)

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('milk_tracker.db'):
            db.create_all()
    app.run(debug=True)
from flask import Flask, render_template, jsonify, request, redirect
from database import total_expense, get_expense, total_income, store_expense,store_income
from markupsafe import Markup
import secrets

app = Flask('__name__')

@app.route('/')
def FinFlex():
  return render_template('index.html')

@app.route('/home')
def home():
  return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def sign():
    return render_template('signup.html')

@app.template_filter('abs')
def filter_abs(value):
    return abs(value)

@app.route('/home/personalfinance', methods=['GET', 'POST'])
def personalfinance():
  if request.method == 'POST':
    form_name = request.form.get('form_name')
    print(form_name)
    if form_name == 'expense':
      category = request.form.get('categoryInput')
      amount = int(request.form.get('amountInput'))
      date_time = request.form.get('dateTimeInput')
      description = request.form.get('descriptionInput')
      store_expense(category, amount, date_time, description)
      return redirect(request.url)
    if form_name == 'income':
      category = request.form.get('categoryInput')
      amount = int(request.form.get('amountInput'))
      date_time = request.form.get('dateTimeInput')
      description = request.form.get('descriptionInput')
      print(category)
      print(amount)
      print(date_time)
      print(description)
      store_income(category, amount, date_time, description)
      return redirect(request.url)
  expense = total_expense()
  income = total_income()
  balance = income - expense
  return render_template('personalfinance.html',
                         total_expense=expense,
                         total_income=income,
                         balance=balance)




app.run(host='0.0.0.0', port=8080)
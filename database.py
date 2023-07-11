from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

import os

my_secret = os.environ['DB_details']

engine = create_engine(my_secret,
                       connect_args={"ssl": {
                         "ssl_ca": "/etc/ssl/cert.pem"
                       }})

Session = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
  __tablename__ = 'users'

  firstname = Column(String(20))
  lastname = Column(String(20))
  email = Column(String(50), unique=True, primary_key=True)
  password = Column(String(50))

  def __init__(self, firstname, lastname, email, password):
    self.firstname = firstname
    self.lastname = lastname
    self.email = email
    self.password = password


def store_expense(user_email, category, amount, date_time, description):
  if not date_time:
    # If date_time is not provided, use the current date and time
    date_time = datetime.now()
  else:
    # Parse the provided date_time string into a datetime object
    date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M')

  # Format the datetime object as a string in the MySQL TIMESTAMP format
  date_time_formatted = date_time.strftime('%Y-%m-%d %H:%M:%S')

  with engine.connect() as conn:
    query = text(
      "INSERT INTO expense (email, category, amount, date_time, description) VALUES (:user_email, :category, :amount, :date_time, :description)"
    )
    conn.execute(
      query, {
        "user_email": user_email,
        "category": category,
        "amount": amount,
        "date_time": date_time_formatted,
        "description": description
      })


def store_income(user_email, category, amount, date_time, description):
  if not date_time:
    # If date_time is not provided, use the current date and time
    date_time = datetime.now()
  else:
    # Parse the provided date_time string into a datetime object
    date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M')

  # Format the datetime object as a string in the MySQL TIMESTAMP format
  date_time_formatted = date_time.strftime('%Y-%m-%d %H:%M:%S')

  with engine.connect() as conn:
    query = text(
      "INSERT INTO income (email, category, amount, date_time, description) VALUES (:user_email, :category, :amount, :date_time, :description)"
    )
    conn.execute(
      query, {
        "user_email": user_email,
        "category": category,
        "amount": amount,
        "date_time": date_time_formatted,
        "description": description
      })


def get_total_expense_and_income(user_email, month_id):
  with engine.connect() as conn:

    # Calculate total expense for the specified month
    expense_query = text(
      "SELECT COALESCE(ROUND(SUM(amount), 2), 0) AS total_expense FROM expense WHERE MONTH(date_time) = :month AND email = :user_email"
    )
    expense_result = conn.execute(expense_query, {
      "month": month_id,
      "user_email": user_email
    })
    total_expense = expense_result.fetchone()[0]

    # Calculate total income for the specified month
    income_query = text(
      "SELECT COALESCE(ROUND(SUM(amount), 2), 0) AS total_income FROM income WHERE MONTH(date_time) = :month AND email = :user_email"
    )
    income_result = conn.execute(income_query, {
      "month": month_id,
      "user_email": user_email
    })
    total_income = income_result.fetchone()[0]

    return total_expense, total_income


def get_transactions(user_email, month_id):
  with engine.connect() as conn:
    transactions_query = text(
      "SELECT 'expense' AS transaction_type, DATE_FORMAT(expense.date_time, '%D %b %Y') AS transaction_date, TIME_FORMAT(expense.date_time, '%r') AS transaction_time, expense.* FROM expense WHERE email = :user_email AND MONTH(expense.date_time) = :month_id    UNION ALL    SELECT 'income' AS transaction_type, DATE_FORMAT(income.date_time, '%D %b %Y') AS transaction_date, TIME_FORMAT(income.date_time, '%r') AS transaction_time, income.* FROM income WHERE email = :user_email AND MONTH(income.date_time) = :month_id    ORDER BY    STR_TO_DATE(CONCAT(transaction_date, ' ', transaction_time), '%D %b %Y %r') ASC"
    )
    result = conn.execute(transactions_query, {
      "month_id": month_id,
      "user_email": user_email
    })
    transactions = []
    ID = 1

    for row in result.all():
      transaction_dict = row._asdict()
      transaction_dict['ID'] = ID
      transactions.append(transaction_dict)
      ID += 1

    return transactions


def store_asset(user_email, category, amount, month_id):
  with engine.connect() as conn:
    query = text(
      "INSERT INTO assets (email, category, amount, month) VALUES (:user_email, :category, :amount, :month_id) "
    )
    conn.execute(query, {
      "user_email": user_email,
      "category": category,
      "amount": amount,
      "month_id": month_id
    })


def store_goal(user_email, amount, month_id, goal_amount):
  with engine.connect() as conn:
    if(goal_amount):
      query = text(
        "UPDATE savings_goal SET amount = :amount WHERE month = :month_id"
      )
    else:
      query = text(
        "INSERT INTO savings_goal (email, amount, month) VALUES (:user_email, :amount, :month_id)"
      )
    conn.execute(
      query, {
        "user_email": user_email,
        "amount": amount,
        "month_id": month_id
      })


def get_assets_and_goal(user_email, month_id):
  with engine.connect() as conn:
    assets_query = text(
      "SELECT category, ROUND(amount, 2) AS rounded_amount FROM assets WHERE email = :user_email")
    assets_result = conn.execute(
      assets_query, {
        "user_email": user_email
      }
    )
    assets = {}

    for row in assets_result:
      category = row.category
      amount = row.rounded_amount

      assets[category] = amount

    goal_query = text(
      "SELECT COALESCE(ROUND(amount, 2), 0) AS rounded_amount FROM savings_goal WHERE month = :month_id AND email = :user_email")
    goal_result = conn.execute(
      goal_query, {
        "month_id": month_id,
        "user_email": user_email
      }
    )

    row = goal_result.fetchone()

    if row is not None:
        goal_amount = float(row[0])
    else:
        goal_amount = None
    
    return assets, goal_amount

def store_debt(user_email, loan_type, loan_provider, amount, interest_rate, duration, paid_amount):
  with engine.connect() as conn:
    store_debt_query = text("INSERT into debt_tracker (email, loan_type, loan_provider, amount, interest, duration, paid) VALUES (:user_email, :loan_type, :loan_provider, :amount, :interest_rate, :duration, :paid_amount)")
    conn.execute(store_debt_query, {
      "user_email": user_email,
      "loan_type": loan_type,
      "loan_provider": loan_provider,
      "amount": amount,
      "interest_rate": interest_rate,
      "duration": duration,
      "paid_amount": paid_amount
    })
def store_debt_paid(user_email, id, amount):
  with engine.connect() as conn:
    store_debt_paid_query = text("UPDATE debt_tracker SET paid = :amount WHERE id = :id")
    conn.execute(store_debt_paid_query, {
      "amount": amount,
      "id": id
    })

def get_debts(user_email):
  with engine.connect() as conn:
    debts_query = text("SELECT * FROM debt_tracker WHERE email = :user_email ORDER BY id DESC")
    result = conn.execute(debts_query, {"user_email": user_email})
    debts = []
    for row in result.all():
      debt_dict = row._asdict()
      if (not debt_dict['paid']):
        (debt_dict['paid'])=0
      debt_dict['remaining'] = ((debt_dict['amount']) + ((debt_dict['amount']) * ((debt_dict['interest'])/100) * ((debt_dict['duration'])/12))) - (debt_dict['paid'])
      debts.append(debt_dict)
    return debts
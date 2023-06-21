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


def get_total_expense_and_income(month_id, user_email):
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


def get_transactions(month_id, user_email):
  with engine.connect() as conn:
    transactions_query = text("SELECT 'expense' AS transaction_type, DATE_FORMAT(expense.date_time, '%D %b %Y') AS transaction_date, TIME_FORMAT(expense.date_time, '%r') AS transaction_time, expense.* FROM expense WHERE email = :user_email AND MONTH(expense.date_time) = :month_id    UNION ALL    SELECT 'income' AS transaction_type, DATE_FORMAT(income.date_time, '%D %b %Y') AS transaction_date, TIME_FORMAT(income.date_time, '%r') AS transaction_time, income.* FROM income WHERE email = :user_email AND MONTH(income.date_time) = :month_id    ORDER BY    STR_TO_DATE(CONCAT(transaction_date, ' ', transaction_time), '%D %b %Y %r') ASC")
    result = conn.execute(transactions_query, {"month_id": month_id, "user_email": user_email})
    transactions = []
    ID = 1

    for row in result.all():
        transaction_dict = row._asdict()
        transaction_dict['ID'] = ID
        transactions.append(transaction_dict)
        ID += 1
    
    return transactions
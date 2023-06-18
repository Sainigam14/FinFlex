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


def get_total_expense_and_income(month_id, year, user_email):
  with engine.connect() as conn:

    # Calculate total expense for the specified month
    expense_query = text(
      "SELECT COALESCE(ROUND(SUM(amount), 2), 0) AS total_expense FROM expense WHERE YEAR(date_time) = :year AND MONTH(date_time) = :month AND email = :user_email"
    )
    expense_result = conn.execute(expense_query, {
      "year": year,
      "month": month_id,
      "user_email": user_email
    })
    total_expense = expense_result.fetchone()[0]

    # Calculate total income for the specified month
    income_query = text(
      "SELECT COALESCE(ROUND(SUM(amount), 2), 0) AS total_income FROM income WHERE YEAR(date_time) = :year AND MONTH(date_time) = :month AND email = :user_email"
    )
    income_result = conn.execute(income_query, {
      "year": year,
      "month": month_id,
      "user_email": user_email
    })
    total_income = income_result.fetchone()[0]

    return total_expense, total_income


def get_transactions(month_id, user_email):
  with engine.connect() as conn:
    transactions_query = text("(SELECT * FROM expense WHERE email = :user_email AND MONTH(date_time) = :month_id)   UNION ALL   (SELECT * FROM income WHERE email = :user_email AND MONTH(date_time) = :month_id)")
    result = conn.execute(transactions_query, {"month_id":month_id, "user_email":user_email})
    transactions = []
    for row in result.all():
      transactions.append(row._asdict())
    return transactions

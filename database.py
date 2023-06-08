from sqlalchemy import create_engine, text, Column, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
my_secret = os.environ['DB_details']

engine = create_engine(my_secret, connect_args={
        "ssl": {
            "ssl_ca": "/etc/ssl/cert.pem"
        }
    })

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

def total_expense(user_email):
    with engine.connect() as conn:
      query = text("SELECT COALESCE(SUM(amount), 0) AS total_amount FROM expense WHERE email = :user_email")
      result = conn.execute(query, {"user_email" : user_email}).fetchone()
      total_amount = result[0]
      return int(total_amount)

def total_income(user_email):
  with engine.connect() as conn:
    query = text("SELECT COALESCE(SUM(amount), 0) AS total_amount FROM income WHERE email = :user_email")
    result = conn.execute(query, {"user_email" : user_email}).fetchone()
    total_amount = result[0]
    return int(total_amount)

def store_expense(user_email, category, amount, date_time, description):
  with engine.connect() as conn:
    query = text("INSERT INTO expense (email, category, amount, date_time, description) VALUES (:user_email, :category, :amount, :date_time, :description)")
    conn.execute(query, {"user_email" : user_email, "category": category, "amount": amount, "date_time": date_time, "description": description})

def store_income(user_email, category, amount, date_time, description):
  with engine.connect() as conn:
    query = text("INSERT INTO income (email, category, amount, date_time, description) VALUES (:user_email, :category, :amount, :date_time, :description)")
    conn.execute(query, {"user_email" : user_email, "category": category, "amount": amount, "date_time": date_time, "description": description})


def get_expense():
  with engine.connect() as conn:
    result = conn.execute(text("select * from expense"))
    expenses = []
    for row in result.all():
      expenses.append(row._asdict())
    return expenses
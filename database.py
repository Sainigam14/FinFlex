from sqlalchemy import create_engine, text

engine = create_engine("mysql+pymysql://m3wmcgloi0pstrejrhsm:pscale_pw_UnURrEs7VX3P16klv9GkWAjvyxroDWsEMhAyPzxL0Fg@aws.connect.psdb.cloud/finflex?charset=utf8mb4", connect_args={
        "ssl": {
            "ssl_ca": "/etc/ssl/cert.pem"
        }
    })

def get_expense():
  with engine.connect() as conn:
    result = conn.execute(text("select * from expense"))
    expenses = []
    for row in result.all():
      expenses.append(row._asdict())
    return expenses

def total_expense():
    with engine.connect() as conn:
      query = text("SELECT COALESCE(SUM(amount), 0) AS total_amount FROM expense")
      result = conn.execute(query).fetchone()
      total_amount = result[0]
      return int(total_amount)

def total_income():
  with engine.connect() as conn:
    result = conn.execute(text("SELECT SUM(amount) AS total_amount FROM income"))
    total_amount = result.all()
    value = int(total_amount[0]._asdict()['total_amount'])
    return value

def store_expense(category, amount, date_time, description):
  with engine.connect() as conn:
    query = text("INSERT INTO expense (category, amount, date_time, description) VALUES (:category, :amount, :date_time, :description)")
    conn.execute(query, {"category": category, "amount": amount, "date_time": date_time, "description": description})

def store_income(category, amount, date_time, description):
  with engine.connect() as conn:
    query = text("INSERT INTO income (category, amount, date_time, description) VALUES (:category, :amount, :date_time, :description)")
    conn.execute(query, {"category": category, "amount": amount, "date_time": date_time, "description": description})

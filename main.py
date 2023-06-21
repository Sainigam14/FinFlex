from flask import Flask, render_template, request, redirect, session, flash, url_for
from database import Session, User, store_expense, store_income, datetime, get_total_expense_and_income, get_transactions
import plotly.graph_objects as go

app = Flask('__name__')
app.secret_key = 'my_secret_key'


@app.route('/')
def FinFlex():
  return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
  month_id = '0' + str((datetime.now().month))
  if request.method == 'POST':
    email = request.form.get('email')
    password = request.form.get('password')

    db_session = Session()
    user = db_session.query(User).filter_by(email=email).first()
    db_session.close()

    if user and user.password == password:
      session['user_email'] = user.email
      return redirect(url_for('home', month_id=month_id))
    elif not user:
      error_message = 'Please create an account'
      return render_template('login.html', error_message=error_message)
    else:
      error_message = 'Invalid password'
      return render_template('login.html', error_message=error_message)
  if 'user_email' in session:
    return redirect(url_for('home', month_id=month_id))

  # User is not logged in, redirect to login page
  return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
  month_id = '0' + str((datetime.now().month))
  if request.method == 'POST':
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    password = request.form.get('password')

    db_session = Session()
    existing_user = db_session.query(User).filter_by(email=email).first()

    if existing_user:
      error_message = 'User already exists. Please log in.'
      db_session.close()
      return render_template('signup.html', error_message=error_message)

    new_user = User(firstname=firstname,
                    lastname=lastname,
                    email=email,
                    password=password)

    db_session.add(new_user)
    db_session.commit()
    db_session.close()

    session['user_email'] = email

    # Redirect to the home page after successful signup
    return redirect(url_for('home', month_id=month_id))
  if 'user_email' in session:
    return redirect(url_for('home', month_id=month_id))

  # Render the signup form for GET requests
  return render_template('signup.html')


@app.template_filter('abs')
def filter_abs(value):
  return abs(value)


# Protected route for the dashboard
@app.route('/home/<month_id>')
def home(month_id):
  if 'user_email' in session:
    user_email = session['user_email']

    db_session = Session()
    user = db_session.get(User, user_email)
    db_session.close()

    #Assests pie chart
    data = {
        'Gold': 10000,
        'Stocks': 5000,
        'Land': 40000,
        'Cash': 10000
    }

    labels = list(data.keys())
    values = list(data.values())

    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5)])

    fig.update_traces(textinfo='none')

    fig.update_layout(
      showlegend=False,  # Remove the legend
      margin=dict(t=0, b=0, l=0, r=0),  # Remove chart margins
      paper_bgcolor='rgba(0,0,0,0)',  # Set chart background color to transparent
      plot_bgcolor=
      'rgba(0,0,0,0)'  # Set plot area background color to transparent
    )

    pie_chart = fig.to_html(full_html=False, config={'displayModeBar': False})

    #Calculating balance for savings goal
    expense, income = get_total_expense_and_income(month_id, user_email)
    balance = income - expense

    return render_template('home.html',
                           user=user,
                           month_id=month_id,
                           pie_chart=pie_chart,
                           balance=balance)

  # User is not logged in, redirect to login page
  return redirect('/login')


@app.route('/home/personalfinance/<month_id>', methods=['GET', 'POST'])
def personalfinance(month_id):
  if 'user_email' in session:
    user_email = session['user_email']
    if request.method == 'POST':
      form_name = request.form.get('form_name')
      if form_name == 'expense':
        category = request.form.get('categoryInput')
        amount = float(request.form.get('amountInput'))
        date_time = request.form.get('dateTimeInput')
        description = request.form.get('descriptionInput')
        store_expense(user_email, category, amount, date_time, description)
        flash('Successfully added expense details', 'success')
        return redirect(url_for('personalfinance', month_id=month_id))
      if form_name == 'income':
        category = request.form.get('categoryInput')
        amount = float(request.form.get('amountInput'))
        date_time = request.form.get('dateTimeInput')
        description = request.form.get('descriptionInput')
        store_income(user_email, category, amount, date_time, description)
        flash('Successfully added income details', 'success')
        return redirect(url_for('personalfinance', month_id=month_id))
    expense, income = get_total_expense_and_income(month_id, user_email)
    balance = income - expense
    return render_template('personalfinance.html',
                           total_expense=expense,
                           total_income=income,
                           balance=balance,
                           month_id=month_id)
  return redirect('/login')


@app.route('/home/transactions/<month_id>')
def transactions(month_id):
  if 'user_email' in session:
    user_email = session['user_email']
    transactions = get_transactions(month_id, user_email)
    return render_template('transactions.html',
                           month_id=month_id,
                           transactions=transactions)
  # User is not logged in, redirect to login page
  return redirect('/login')


@app.route('/home/blog')
def blog():
  if 'user_email' in session:
    return render_template('blog.html')
  # User is not logged in, redirect to login page
  return redirect('/login')


@app.route('/home/personalfinance/signout')
def signout():
  session.clear()
  return redirect('/')


app.run(host='0.0.0.0', port=8080)
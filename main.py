from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_bcrypt import Bcrypt
from database import Session, User, store_expense, store_income, datetime, get_total_expense_and_income, get_transactions, store_asset, store_goal, get_assets_and_goal, get_debts
import plotly.graph_objects as go
import plotly.express as px

app = Flask('__name__')
bcrypt = Bcrypt(app)
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

    is_valid = bcrypt.check_password_hash(user.password, password)
    print(is_valid)

    if user and is_valid:
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
    h_password = bcrypt.generate_password_hash(password).decode('utf-8')

    db_session = Session()
    existing_user = db_session.query(User).filter_by(email=email).first()

    if existing_user:
      error_message = 'User already exists. Please log in.'
      db_session.close()
      return render_template('signup.html', error_message=error_message)

    new_user = User(firstname=firstname,
                    lastname=lastname,
                    email=email,
                    password=h_password)

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
@app.route('/home/<month_id>', methods=['GET', 'POST'])
def home(month_id):
  if 'user_email' in session:
    user_email = session['user_email']

    assets, goal_amount = get_assets_and_goal(user_email, month_id)

    if request.method == 'POST':
      form_name = request.form.get('form_name')
      if form_name == 'assets':
        category = request.form.get('categoryInput')
        amount = float(request.form.get('amountInput'))
        print(user_email, category, amount)
        store_asset(user_email, category, amount)
        return redirect(url_for('home', month_id=month_id))

      if form_name == 'goal':
        category = request.form.get('categoryInput')
        amount = float(request.form.get('amountInput'))
        store_goal(user_email, amount, month_id, goal_amount)
        return redirect(url_for('home', month_id=month_id))

    db_session = Session()
    user = db_session.get(User, user_email)
    db_session.close()

    # Assests pie chart
    labels = list(assets.keys())
    values = list(assets.values())

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

    # Calculating balance for savings goal
    expense, income = get_total_expense_and_income(user_email, month_id)
    balance = income - expense

    # Bar graph for Income sources
    income_sources = ['Business', 'Gift', 'Scholarship', 'Salary']
    values = [35128.12, 10000, 5635, 50000]

    fig = px.bar(x=income_sources, y=values, text=values, color=income_sources)

    fig.update_traces(
      texttemplate=
      '%{text:.2f}',  # Display the y-label as a floating-point number with two decimal places
      textposition='outside',
      cliponaxis=False,
      hovertemplate='<b>%{x}</b><br>' +
      '%{y}<extra></extra>'  # Display the y-label as a floating-point number with two decimal places
    )

    fig.update_xaxes(
      title=None,
      tickangle=0,
      showticklabels=True,
      ticktext=['', '', ''],  # Empty labels for ticks
      tickwidth=1,  # Width of the bottom border
      tickcolor='blue'  # Color of the bottom border
    )

    fig.update_yaxes(
      visible=False
    )

    fig.update_layout(title=None,
                      showlegend=False,
                      width=235,
                      height=140,
                      margin=dict(t=15, b=0, l=0, r=0),
                      plot_bgcolor='rgba(0, 0, 0, 0)',
                      bargap=0.5,
                      uniformtext=dict(minsize=12, mode='show'))

    sources_graph = fig.to_html(full_html=False,
                                config={'displayModeBar': False})

    return render_template('home.html',
                           user=user,
                           month_id=month_id,
                           sources_graph=sources_graph,
                           pie_chart=pie_chart,
                           balance=balance,
                           goal_amount=goal_amount,
                           assets=assets)

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
    expense, income = get_total_expense_and_income(user_email, month_id)
    balance = income - expense
    return render_template('personalfinance.html',
                           total_expense=expense,
                           total_income=income,
                           balance=balance,
                           month_id=month_id)
  return redirect('/login')

@app.route('/home/debttracker/<month_id>', methods=['GET','POST'])
def debttracker(month_id):
  if 'user_email' in session:
    user_email = session['user_email']
    if request.method == 'POST':
      pass

    # Debt Tracker pie chart
    debts = get_debts(user_email)
    labels = []
    values = []
    for debt in debts:
      labels.append(debt['loan_provider']+'('+debt['loan_type']+')')
      values.append(debt['amount'])
    
    # Create a pie chart
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.5)])
    
    # Update trace settings
    fig.update_traces(textinfo='none')
    
    # Update layout settings
    fig.update_layout(
      showlegend=False,  # Remove the legend
      margin=dict(t=0, b=0, l=0, r=0),  # Remove chart margins
      paper_bgcolor='rgba(0,0,0,0)',  # Set chart background color to transparent
      plot_bgcolor=
      'rgba(0,0,0,0)'  # Set plot area background color to transparent
    )
    
    # Generate the HTML code for the chart
    debt_chart = fig.to_html(full_html=False, config={'displayModeBar': False})

    
    # Pass the chart to the template
    return render_template('debttracker.html', month_id=month_id, debt_chart=debt_chart, debts=debts)

  return redirect('/login')

@app.route('/home/transactions/<month_id>')
def transactions(month_id):
  if 'user_email' in session:
    user_email = session['user_email']
    transactions = get_transactions(user_email, month_id)
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

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=8080)
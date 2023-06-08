from flask import Flask, render_template, jsonify, request, redirect, session
from database import engine, Session, User, total_expense, get_expense, total_income, store_expense,store_income

app = Flask('__name__')
app.secret_key = 'my_secret_key'

@app.route('/')
def FinFlex():
  return render_template('index.html')

@app.route('/signup')
def sign():
    return render_template('signup.html')

@app.template_filter('abs')
def filter_abs(value):
    return abs(value)
  
# Protected route for the dashboard
@app.route('/home')
def home():
  if 'user_email' in session:
        user_email = session['user_email']

        db_session = Session()
        user = db_session.get(User, user_email)
        db_session.close()

        return render_template('home.html', user=user)

    # User is not logged in, redirect to login page
  return redirect('/login')
  
@app.route('/home/personalfinance', methods=['GET', 'POST'])
def personalfinance():
  if 'user_email' in session:
    user_email = session['user_email']
    if request.method == 'POST':
      form_name = request.form.get('form_name')
      if form_name == 'expense':
        category = request.form.get('categoryInput')
        amount = int(request.form.get('amountInput'))
        date_time = request.form.get('dateTimeInput')
        description = request.form.get('descriptionInput')
        store_expense(user_email, category, amount, date_time, description)
        return redirect('/home/personalfinance?message=Successfully added expense details')
      if form_name == 'income':
        category = request.form.get('categoryInput')
        amount = int(request.form.get('amountInput'))
        date_time = request.form.get('dateTimeInput')
        description = request.form.get('descriptionInput')
        store_income(user_email, category, amount, date_time, description)
        return redirect('/home/personalfinance?message=Successfully added income details')
    expense = total_expense(user_email)
    income = total_income(user_email)
    balance = income - expense
    print(balance)
    return render_template('personalfinance.html',
                           total_expense=expense,
                           total_income=income,
                           balance=balance)
  return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        db_session = Session()
        user = db_session.query(User).filter_by(email=email).first()
        db_session.close()

        if user and user.password == password:
            session['user_email'] = user.email
            return redirect('/home')
        elif not user:
            error_message = 'Please create an account'
            return render_template('login.html', error_message=error_message)
        else:
            error_message = 'Invalid password'
            return render_template('login.html', error_message=error_message)
          
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
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

        new_user = User(firstname=firstname, lastname=lastname, email=email, password=password)

        db_session.add(new_user)
        db_session.commit()
        db_session.close()

        session['user_email'] = email

        # Redirect to the login page after successful signup
        return redirect('/home')

    # Render the signup form for GET requests
    return render_template('signup.html')



@app.route('/home/personalfinance/signout')
def signout():
  session.clear();
  return redirect('/')



app.run(host='0.0.0.0', port=8080)
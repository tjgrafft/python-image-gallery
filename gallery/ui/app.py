from flask import Flask, session, render_template, request, redirect, url_for, flash
from functools import wraps
from gallery.tools.db import DbConnection
from ..data.user import User
from ..data.postgres_user_dao import PostgresUserDAO
from gallery.tools.secrets import get_secret_flask_session

app = Flask(__name__)
app.secret_key = get_secret_flask_session()['secret_key']

def get_user_dao():
    return PostgresUserDAO

def check_admin():
    return 'username' in session and session['username'] == 'barney'

def check_user():
    return 'username' in session

def requires_admin(view):
    @wraps(view)
    def decorated(**kwags):
        if not check_admin():
            return redirect('/login')
        return view(**kwags)
    return decorated

def requires_login(view):
    @wraps(view)
    def decorated(**kwags):
        if not check_user():
            return redirect('/login')
        return view(**kwags)
    return decorated

db = DbConnection()
db.connect()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user_dao().get_user_by_username(request.form['username'])
        if user is None or user.password != request.form['password']:
            flash('Invalid username or password')
            return redirect('/login')
        else: 
            session['username'] = request.form['username']
            return redirect('/')
    else:
        return render_template('login.html')

@app.route('/admin/users')
@requires_admin
def admin():
    #db = DbConnection()
    #db.connect()
    #users = db.execute('SELECT username, full_name FROM users').fetchall()
    return render_template('admin.html', users=get_user_dao().get_users())

@app.route('/admin/addUser', methods=['GET', 'POST'])
@requires_admin
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        fullname = request.form['full_name']

        db = DbConnection()
        db.connect()
        db.execute("INSERT INTO users (username, password, full_name) VALUES (%s, %s, %s)", (username, password, fullname))
        db.connection.commit()

        return redirect(url_for('admin'))

    return render_template('add_user.html')

@app.route('/admin/editUser/<username>', methods=['GET', 'POST'])
@requires_admin
def edit_user(username):
    db = DbConnection()
    db.connect()

    if request.method == 'POST':
        new_password = request.form['password']
        new_fullname = request.form['full_name']

        db.execute("UPDATE users SET password = %s, full_name = %s WHERE username = %s", (new_password, new_fullname, username))
        db.connection.commit()

        return redirect(url_for('admin'))

    user = db.execute("SELECT * FROM users WHERE username = %s", (username,)).fetchone()
    return render_template('edit_user.html', user=user)

@app.route('/admin/deleteUser/<username>')
@requires_admin
def delete_user(username):
    #db = DbConnection()
    #db.connect()
    #db.execute("DELETE FROM users WHERE username = %s", (username,))
    #db.connection.commit()
    get_user_dao().delete_user(username)
    return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run()
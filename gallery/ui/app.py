from flask import Flask, render_template, request, redirect, url_for
from db import DbConnection

app = Flask(__name__)

@app.route('/admin')
def admin():
    db = DbConnection()
    db.connect()
    users = db.execute('SELECT username, full_name FROM users').fetchall()
    return render_template('admin.html', users=users)

@app.route('/admin/addUser', methods=['GET', 'POST'])
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
def delete_user(username):
    db = DbConnection()
    db.connect()
    db.execute("DELETE FROM users WHERE username = %s", (username,))
    db.connection.commit()

    return redirect(url_for('admin'))

if __name__ == "__main__":
    app.run()
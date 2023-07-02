from flask import Flask, session, render_template, request, redirect, url_for, flash, send_from_directory
from functools import wraps
from gallery.tools.db import DbConnection
from ..data.user import User
from ..data.postgres_user_dao import PostgresUserDAO
from gallery.tools.secrets import get_secret_flask_session
from werkzeug.utils import secure_filename
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os
import logging
import json
from gallery.tools.s3 import put_object

app = Flask(__name__)

def read_cookie_from_aws():
    json_string2 = get_secret_flask_session()
    return json.loads(json_string2)


app.secret_key = read_cookie_from_aws()['secret_key']

UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

def upload_to_s3(file):
    try:
        with open(f'/tmp/{file}', 'rb') as data:
            put_object('edu.au.cs.image-gallery2', f'{session["username"]}/{file}', data)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


db = DbConnection()
db.connect()

@app.route('/')
def home():
    return '''
    <h1>Welcome to the Image Gallery</h1>
    <ul>
        <li><a href="/upload">Upload Image</a></li>
        <li><a href="/view_images">View Images</a></li>
        <li><a href="/admin/users">Admin</a></li>
    </ul
    '''

@app.route('/upload', methods=['GET', 'POST'])
@requires_login
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            if upload_to_s3(filename):
                db.execute("insert into images (filename, owner) values (%s, %s)", (filename, session['username']))
                db.connection.commit()
            return redirect('/')
    return render_template('upload.html')    

@app.route('/view_images')
@requires_login
def view_images():
    s3 = boto3.client('s3')
    images = db.execute("select filename from images where owner = %s", (session['username'],)).fetchall()
    urls = []
    for image in images:
        url = s3.generate_presigned_url('get_object', Params = {'Bucket': 'edu.au.cs.image-gallery2', 'Key': image['filename']}, ExpiresIn = 100)
        urls.append(url)
    return render_template('view_images.html', urls=urls)

@app.route('/delete_image/<filename>', methods=['POST'])
@requires_login
def delete_image(filename):
    owner = db.execute("SELECT owner FROM images WHERE filename = %s", (filename,)).fetchone()[0]
    if owner != session['username']:
        flash('You do not have permission to delete this image.')
        return redirect(url_for('view_images'))
    s3 = boto3.client('s3')
    try:
        s3.delete_object(Bucket='edu.au.cs.image-gallery2', Key=f'{session["username"]}/{filename}')
    except ClientError as e:
        logging.error(e)
        flash('Failed to delete image from S3.')
        return redirect(url_for('view_images'))
    db.execute("DELETE FROM images WHERE filename = %s", (filename,))
    db.connection.commit()
    flash('Image deleted successfully.')
    return redirect(url_for('view_images'))


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

        return redirect('/admin/users')

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

        return redirect('/admin/users')

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
    return redirect('/admin/users')

if __name__ == "__main__":
    app.run()
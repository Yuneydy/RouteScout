from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
import cs304login as login

# import cs304dbi_sqlite3 as dbi

import secrets

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

@app.route('/', methods = ["GET", "POST"])
def login():
     if request.method == "GET":
        return render_template('login.html')
     else:
        conn = dbi.connect()
        user = request.form.get("username")
        passwrd = request.form.get("password")
        success = login.login_user(conn, user, passwrd)
        if success[0] == True:
                return render_template('profileFeed.html')
              
@app.route('/join/', methods = ["GET", "POST"])
def signup():
      if request.method == "GET":
            return render_template('signup.html')
      else:
                conn = dbi.connect()
                user = request.form.get("username")
                passwrd1 = request.form.get("password1")
                passwrd2 = request.form.get("password2")
                success = login.insert_user(conn, user, passwrd1, verbose=False)
                return render_template('signup.html')

        

# You will probably not need the routes below, but they are here
# just in case. Please delete them if you are not using them

@app.route('/upload_route/', methods=["GET", "POST"])
def upload_route():
        return render_template('routeForm.html')
@app.route('/search_route/', methods=["GET", "POST"])
def search_route():
        return render_template('routeSearch.html')
@app.route('/profile/', methods=["GET", "POST"])
def profile():
        return render_template('profile.html')
@app.route('/profileFeed/', methods=["GET", "POST"])
def profileFeed():
        return render_template('profileFeed.html')
@app.route('/aboutUs/', methods=["GET", "POST"])
def aboutUs():
        return render_template('aboutUs.html')


@app.route('/ranRoute/', methods=["GET", "POST"])
def ranRoute():
        if request.method == "GET":
                return render_template('ranRoute.html')
        else: 
                routeNum = request.form.get('route_ID')
                routeRating = request.form.get('rating')
                routeComment = request.form.get('comment')
                num = int(routeNum)
                rating = int(routeRating)
                conn = dbi.connect()
                curs = dbi.cursor(conn)
                curs.execute(
                'INSERT INTO route_rating(routeID, rating, comment) VALUES (%s, %s, %s)',
                (routeNum, routeRating, routeComment)) 
                conn.commit()
                return render_template('ranRoute.html')
      
    

# This route displays all the data from the submitted form onto the rendered page
# It's unlikely you will ever need anything like this in your own applications, so
# you should probably delete this handler

@app.route('/formecho/', methods=['GET','POST'])
def formecho():
    if request.method == 'GET':
        return render_template('form_data.html',
                               page_title='Display of Form Data',
                               method=request.method,
                               form_data=request.args)
    elif request.method == 'POST':
        return render_template('form_data.html',
                               page_title='Display of Form Data',
                               method=request.method,
                               form_data=request.form)
    else:
        raise Exception('this cannot happen')

# This route shows how to render a page with a form on it.

@app.route('/testform/')
def testform():
    # these forms go to the formecho route
    return render_template('testform.html',
                           page_title='Page with two Forms')


if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        # arg, if any, is the desired port number
        port = int(sys.argv[1])
        assert(port>1024)
    else:
        port = os.getuid()
    # set this local variable to 'wmdb' or your personal or team db
    db_to_use = 'routesct_db' 
    print(f'will connect to {db_to_use}')
    dbi.conf(db_to_use)
    app.debug = True
    app.run('0.0.0.0',port)
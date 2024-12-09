from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
# one or the other of these. Defaults to MySQL (PyMySQL)
# change comment characters to switch to SQLite

import cs304dbi as dbi
import bcrypt

# import cs304dbi_sqlite3 as dbi
import queries as q
import secrets
import os

app.secret_key = 'your secret here'
# replace that with a random key
app.secret_key = secrets.token_hex()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Set up upload folder
upload_path = os.path.join(os.getcwd(), 'static/uploads')
if not os.path.exists(upload_path):
    os.makedirs(upload_path)  # Create the directory if it doesn't exist
app.config['UPLOAD_FOLDER'] = upload_path

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# Initial page titled RouteScout that gives you the option of login or sign up
@app.route('/', methods=["POST", "GET"])
def intro():
       if request.method == "GET":
              return render_template('intro.html')
       else:
              action = request.form.get('submit')
              if action == "login":
                return redirect(url_for('login'))
              else:
                return redirect(url_for('signUp'))

# Allows users to login to the website with their username and login, if the
# login is successful, the user is redirected to their profile feed page
@app.route('/login/', methods=["POST", "GET"])
def login():
    if request.method == "GET":
          return render_template('login.html')
    else:
        username = request.form.get('username')
        passwd = request.form.get('password')
        conn = dbi.connect()
        curs = dbi.dict_cursor(conn)
        curs.execute('''SELECT uid,hashed
                        FROM userpass
                        WHERE username = %s''',
                        [username])
        row = curs.fetchone()
        if row is None:
                # Same response as wrong password,
                # so no information about what went wrong
                flash('login incorrect. Try again or join')
                return redirect( url_for('login'))
        stored = row['hashed']
        uid = row['uid']
        print('LOGIN', username)
        print('database has stored: {} {}'.format(stored,type(stored)))
        print('form supplied passwd: {} {}'.format(passwd,type(passwd)))
        hashed2 = bcrypt.hashpw(passwd.encode('utf-8'),
                                stored.encode('utf-8'))
        hashed2_str = hashed2.decode('utf-8')
        print('rehash is: {} {}'.format(hashed2_str,type(hashed2_str)))
        if hashed2_str == stored:
                print('they match!')
                flash('successfully logged in as '+username)
                session['username'] = username
                session['uid'] = row['uid']
                session['logged_in'] = True
                session['visits'] = 1
                return redirect(url_for('profile', uid=session.get('uid')))
        else:
                flash('login incorrect. Try again or join')
                return redirect( url_for('login'))

# Allows users to create username and password, they will also fill out a form
# where they input their pronouns, average time, overall mileage, and level
@app.route('/join/', methods = ["GET", "POST"])
def signUp():
    if request.method == "GET":
          return render_template('signup.html')
    else:
        username = request.form.get('username')
        passwd1 = request.form.get('password1')
        passwd2 = request.form.get('password2')
        if passwd1 != passwd2:
                flash('passwords do not match')
                return redirect( url_for('index'))
        hashed = bcrypt.hashpw(passwd1.encode('utf-8'),
                                bcrypt.gensalt())
        stored = hashed.decode('utf-8')
        print('JOIN', username, passwd1, stored)
        conn = dbi.connect()
        curs = dbi.cursor(conn)
        try:
                curs.execute('''INSERT INTO userpass(uid,username,hashed)
                                VALUES(null,%s,%s)''',
                        [username, stored])
                conn.commit()
        except Exception as err:
                flash('That username is taken: {}'.format(repr(err)))
                return redirect(url_for('signUp'))
        curs.execute('select last_insert_id()')
        row = curs.fetchone()
        uid = row[0]
        flash('FYI, you were issued UID {}'.format(uid))
        session['username'] = username
        session['uid'] = uid
        session['logged_in'] = True
        session['visits'] = 1

        pronouns = request.form.get('pronouns')
        level = request.form.get('level')
        overallMileage = request.form.get('overall_mileage')
        avgPaceHour = request.form.get('average_pace_hour')
        avgPaceMin = request.form.get('average_pace_min')
        avgPaceOverall = avgPaceHour + avgPaceMin

        conn = dbi.connect()
        curs = dbi.cursor(conn)
        insertUserQuery = 'INSERT into user (uid, username, pronouns, level, overall_mileage, average_pace, routes_created) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        try:
                curs.execute(insertUserQuery, (uid, username, pronouns, level, overallMileage, avgPaceOverall, 0))
                conn.commit()
        except Exception as err:
                print(f'Error inserting into user: {err}')
                flash('Failed to create user profile')
                return redirect(url_for('signUp'))
        return redirect( url_for('profile', uid=uid))

# Logs users out of the website and redirects them back to the route scout intro page
# where they will have the choice to sign up or log in
@app.route('/logout/', methods = ["GET", "POST"])
def logout():
   uid = session.get('uid')
   if (uid is None):
          return redirect(url_for('intro'))
   if request.method == "GET":
         return render_template('logout.html')
   else:
       if 'username' in session:
               username = session['username']
               session.pop('username')
               session.pop('uid')
               session.pop('logged_in')
               flash('You are logged out')
               return redirect(url_for('login'))
       else:
               flash('you are not logged in. Please login or join')
               return redirect(url_for('intro') )


# Allows users to upload their route
@app.route('/upload_route/', methods=["GET", "POST"])
def upload_route():
       uid = session.get('uid')
       if (uid is None):
          return redirect(url_for('intro'))
       if request.method == "GET":
               return render_template('routeForm.html')
       else: # Get data from the form
               conn = dbi.connect()

               #route upload
               routeName = request.form.get("name")
               routeDescrip = request.form.get("notes")
               routeTcx = request.files.get("route_tcx")
               embeddedMap = request.form.get("embedded_map_link")
               levelRun = request.form.get("difficulty")
               mile = request.form.get("distance")
               startTow = request.form.get("starting_town")
               endTow = request.form.get("finishing_town")
               outAndBack = request.form.get("outBack")
               bathr = request.form.get("bathrooms")
               bathDescrip = request.form.get("bathroom_location")
               waterFount = request.form.get("water")
               fountDescrip = request.form.get("water_location")
               numMile = float(mile)

               if routeTcx:
                     nameOfFile = secure_filename(routeTcx.filename)
                     path = os.path.join(app.config['UPLOAD_FOLDER'], nameOfFile)
                     routeTcx.save(path)
                     app.logger.info(f'File saved at {path}')
                     flash('Route file uploaded successfully: ' + nameOfFile)

                     
               curs = dbi.cursor(conn)
               query = '''INSERT INTO route_info(name, route_description, route_tcx, embedded_map_link, level, mileage, 
                starting_location, starting_town, finishing_location, finishing_town, out_and_back, 
                bathroom, bathroom_description, water_fountain, fountain_description, addedBy) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
               curs.execute(query, (routeName, routeDescrip, None, embeddedMap, levelRun, numMile, 
                             None, startTow, None, endTow, outAndBack, bathr, bathDescrip, waterFount, fountDescrip, uid))
               
               #updates profile page, adding one to the number of runs you have created
               query_currentNumber = 'SELECT routes_created from user WHERE uid = %s'
               curs.execute(query_currentNumber, uid)
               row1 = curs.fetchone()
               currentNumber = int(row1[0])
               newNumber = currentNumber + 1
               query_newNumber = 'UPDATE user SET routes_created = %s WHERE uid = %s'
               curs.execute(query_newNumber, (newNumber, uid))

               conn.commit()
               flash('Your route has been submitted! Thank you!')
               return render_template('routeForm.html', uid=uid)

#Search page for routes
@app.route('/routeSearch/', methods=["GET", "POST"])
def search_route():
        uid = session.get('uid')
        if (uid is None):
          return redirect(url_for('intro'))
        conn = dbi.connect()
        if request.method == 'POST':
                route = request.form.get("name")
                level = request.form.get("level")
                mile = request.form.get("mileage")
                startTown = request.form.get("starting_town")
                endTown = request.form.get("finishing_town")
                outBack = request.form.get("out_and_back")
                bath = request.form.get("bathroom")
                waterFount = request.form.get("water_fountain")

                routes = q.get_routes(conn, route, level, mile, startTown, endTown, outBack, bath, waterFount)
                print(routes)
                ratings = q.get_all_ratings(conn)
                avg_ratings = q.get_avg_rating(conn)
                return render_template('routeSearch.html', routes=routes, uid=uid, ratings=ratings, avg_ratings=avg_ratings)
        else:
                routes = q.get_all_routes(conn)
                ratings = q.get_all_ratings(conn)
                avg_ratings = q.get_avg_rating(conn)
                return render_template('routeSearch.html', routes=routes, uid=uid, ratings=ratings, avg_ratings=avg_ratings)

# Shows user their own profile information
@app.route('/profile/', methods=["GET", "POST"])
def profile():
       uid = session.get('uid')
       if (uid is None):
          return redirect(url_for('intro'))
       conn = dbi.connect()
       curs = dbi.dict_cursor(conn)
       findUserNamequery = 'SELECT username from userpass where uid=%s'
       curs.execute(findUserNamequery, uid)
       row = curs.fetchone()
       print(row)
       username = row['username']
       findUserInfoquery = 'select * from user where uid=%s'
       curs.execute(findUserInfoquery, uid)
       row = curs.fetchone()
       print(row)
       pronouns = row['pronouns']
       level = row['level']
       overallMileage = row['overall_mileage']
       averagePace = row['average_pace']
       routesCreated = row['routes_created']
       if request.method == 'GET':
        return render_template(
            'profile.html',
            username=username,
            pronouns=pronouns,
            level=level,
            overallMileage=overallMileage,
            averagePace=averagePace,
            routesCreated=routesCreated
        )
       
       if request.method == 'POST':
             action = request.form.get('submit')
             if action == "update":
                conn = dbi.connect()
                curs = dbi.dict_cursor(conn)
                newUserName = request.form.get('new-username')
                newPronouns = request.form.get('new-pronouns')
                newLevel = request.form.get('new-level')
                newPace = request.form.get('new-pace')
                updateUserQuery = ''' update user 
                set username = %s, pronouns = %s, level = %s, average_pace = %s 
                where uid = %s
                '''
                curs.execute(updateUserQuery, (newUserName, newPronouns, newLevel, newPace, uid))
                conn.commit()
                updateUserPassQuery = 'update userpass set username = %s where uid = %s'
                curs.execute(updateUserPassQuery, (newUserName, uid))
                conn.commit()
                flash('Profile updated successfully')
                return redirect(url_for('profile'))
             else:
                conn = dbi.connect()
                curs = dbi.dict_cursor(conn)
                deleteFromUser = 'delete from user where uid=%s'
                curs.execute(deleteFromUser, [uid])
                conn.commit()
                deleteFromUserPass = 'delete from userpass where uid=%s'
                curs.execute(deleteFromUserPass, [uid])
                conn.commit()
                flash('Account deleted successfully')
                return redirect(url_for('intro'))
                

#Displays all routes or just the routes the user has created
@app.route('/profileFeed/', methods=["GET", "POST"])
def profileFeed():
       uid = session.get('uid')
       if (uid is None):
          return redirect(url_for('intro'))
       conn = dbi.connect()
       filter_option = request.args.get("filter")


       if filter_option == "user":
               user_id = uid
               routes = q.get_user_routes(conn, user_id)
       else:
               routes = q.get_all_routes(conn)
        
       ratings = q.get_all_ratings(conn)
       avg_ratings = q.get_avg_rating(conn)
       print(ratings)
       return render_template('profileFeed.html', routes=routes, ratings=ratings, avg_ratings=avg_ratings)

# Gives informations about creators
@app.route('/aboutUs/', methods=["GET", "POST"])
def aboutUs():
       uid = session.get('uid')
       if (uid is None):
          return redirect(url_for('intro'))
       return render_template('aboutUs.html')

# Allows users to say which routes they have completed and give them a rating
# and a comment
@app.route('/routeSearch/', methods=["GET", "POST"])
def ranRoute():
    uid = session.get('uid')
    if uid is None:
        return redirect(url_for('intro'))
    
    if request.method == "GET":
        return render_template('routeSearch.html')
    else:
        # Get info from the form
        routeNum = request.form.get('route_ID')  # Assuming a hidden or separate input for route_ID
        routeRating = request.form.get('rating') 
        routeComment = request.form.get('comment')

        # Ensure valid inputs
        if not routeNum or not routeRating:
            flash('Route number and rating are required.')
            return redirect(url_for('ranRoute'))

        try:
            # Convert to integers where applicable
            num = int(routeNum)
            rating = int(routeRating)
        except ValueError:
            flash('Invalid data provided for route number or rating.')
            return redirect(url_for('ranRoute'))

        conn = dbi.connect()
        curs = dbi.cursor(conn)

        # Insert into route_rating table
        query_rating = 'INSERT INTO route_rating(uid, routeID, rating, comment) VALUES (%s, %s, %s, %s)'
        curs.execute(query_rating, (uid, num, rating, routeComment))

        # Find mileage of the run
        query_findMileage = 'SELECT mileage FROM route_info WHERE routeID = %s'
        curs.execute(query_findMileage, (num,))
        row = curs.fetchone()
        if row is None:
            flash('Route not found in database.')
            return redirect(url_for('ranRoute'))
        
        routeMileage = row[0]

        # Get the user's current mileage
        query_currentMileage = 'SELECT overall_mileage FROM user WHERE uid = %s'
        curs.execute(query_currentMileage, (uid))
        row1 = curs.fetchone()
        if row1 is None:
            flash('User information not found.')
            return redirect(url_for('ranRoute'))
        
        currentM = float(row1[0])
        newMileage = currentM + routeMileage

        # Update user's overall mileage
        query_newMileage = 'UPDATE user SET overall_mileage = %s WHERE uid = %s'
        curs.execute(query_newMileage, (newMileage, uid))
        conn.commit()

        flash('Your route review has been submitted, and your overall mileage has been updated! Thank you!')
        return redirect(url_for('routeSearch'))


      
    
# This route displays all the data from the submitted form onto the rendered page
# It's unlikely you will ever need anything like this in your own applications, so
# you should probably delete this handler

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
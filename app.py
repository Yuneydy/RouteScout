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
app.config['MAX_CONTENT_LENGTH'] = 1*1024*1024 # 1 MB

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
                flash('login incorrect. Try again or join')
                return redirect( url_for('login'))
        stored = row['hashed']
        uid = row['uid']
        print('LOGIN', username)
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
        session['username'] = username
        session['uid'] = uid
        session['logged_in'] = True
        session['visits'] = 1

        pronouns = request.form.get('pronouns')
        level = request.form.get('level')
        overallMileage = request.form.get('overall_mileage')
        avgPaceHour = request.form.get('average_pace_min')
        avgPaceMin = request.form.get('average_pace_sec')
        avgPaceOverall = avgPaceHour + avgPaceMin
        if len(avgPaceOverall)<4:
              avgPaceOverall = "0"+avgPaceOverall
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
               routeTcx = request.files.get("route_gpx")


               if routeTcx:
                     app.logger.info(f'File received: {routeTcx.filename}')
               else:
                    app.logger.warning('No file received in the request') 


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
                     routeTcxPath = f'uploads/{nameOfFile}'
                     print("here is routeTcxPath: ", routeTcxPath)
                

               uid = session.get('uid')
               if uid is None:
                     app.logger.error ('No user with this id')
               curs = dbi.cursor(conn)
               query = '''INSERT INTO route_info(name, route_description, route_gpx, embedded_map_link, level, mileage, 
                starting_location, starting_town, finishing_location, finishing_town, out_and_back, 
                bathroom, bathroom_description, water_fountain, fountain_description, addedBy) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
               curs.execute(query, (routeName, routeDescrip, routeTcxPath, embeddedMap, levelRun, numMile, 
                             None, startTow, None, endTow, outAndBack, bathr, bathDescrip, waterFount, fountDescrip, uid))
               
               #updates profile page, adding one to the number of runs you have created
               query_newNumber = 'UPDATE user SET routes_created = routes_created+1 WHERE uid = %s'
               curs.execute(query_newNumber, (uid))
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
       username = row['username']
       findUserInfoquery = '''select pronouns, level, overall_mileage, average_pace, routes_created from user where uid=%s'''
       curs.execute(findUserInfoquery, uid)
       row = curs.fetchone()
       findUserProfilePic = '''select profilepictures.profilefilename from profilepictures inner join user on profilepictures.uid=user.uid where user.uid=%s'''
       curs.execute(findUserProfilePic, uid)
       row2 = curs.fetchone()
       if row2:
            profilepicturefilename = row2['profilefilename']
       else:
            profilepicturefilename = "NoProfilePicture.jpeg"
       pronouns = row['pronouns']
       level = row['level']
       overallMileage = row['overall_mileage']
       averagePace = row['average_pace']
       avgPaceMin = averagePace[:2]
       avgPaceSec = averagePace[2:]
       routesCreated = row['routes_created']

       if request.method == 'GET':
        return render_template(
            'profile.html',
            username=username,
            pronouns=pronouns,
            level=level,
            overallMileage=overallMileage,
            avgPaceMin=avgPaceMin,
            avgPaceSec=avgPaceSec,
            routesCreated=routesCreated,
            profilepicturefilename=profilepicturefilename
        )
       
       if request.method == 'POST':
             action = request.form.get('submit')
             if action == "update":
                newUserName = request.form.get('new-username')
                newPronouns = request.form.get('new-pronouns')
                newLevel = request.form.get('new-level')
                if (newLevel != "Beginner") and (newLevel != "Intermediate") and (newLevel != "Advanced"):
                        flash('Level must be Beginner, Intermediate, or Advanced')
                        return redirect(url_for('profile'))
                newPaceMin = request.form.get('new-pace-min')
                if len(newPaceMin) == 1:
                     newPaceMin = "0"+newPaceMin
                newPaceSec = request.form.get('new-pace-sec')
                if len(newPaceSec) == 1:
                     flash('Seconds must be 2 numbers!')
                     return redirect(url_for('profile'))
                newPace = newPaceMin+newPaceSec
                updateUserQuery = ''' update user 
                set username = %s, pronouns = %s, level = %s, average_pace = %s 
                where uid = %s
                '''
                curs.execute(updateUserQuery, (newUserName, newPronouns, newLevel, newPace, uid))
                conn.commit()
                updateUserPassQuery = 'update userpass set username = %s where uid = %s'
                curs.execute(updateUserPassQuery, (newUserName, uid))
                conn.commit()
                try:
                   newprofile = request.files['profilepic'] 
                   if newprofile:
                        user_filename = newprofile.filename
                        ext = user_filename.split('.')[-1]
                        filename = secure_filename('{}.{}'.format(uid,ext))
                        pathname = os.path.join(app.config['UPLOAD_FOLDER'],filename)
                        newprofile.save(pathname)
                        curs.execute(
                                '''insert into profilepictures(uid, profilefilename) values (%s,%s)
                                on duplicate key update profilefilename = %s''',
                                [uid, filename, filename])
                        conn.commit()
                        flash('Upload successful')
                except Exception as err:
                   flash('Upload failed {why}'.format(why=err))
                   return redirect(url_for('profile'))
                
                flash('Profile updated successfully')
                return redirect(url_for('profile'))
             else:
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
               routes = q.get_user_routes(conn, uid)
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

# Gives informations about top users and top runs
@app.route('/rankings/', methods=["GET", "POST"])
def ranking():
       uid = session.get('uid')
       if (uid is None):
          return redirect(url_for('intro'))
       conn = dbi.connect()
       topUsers = q.get_top_users(conn)
       topRoutes = q.get_top_routes(conn)
       topRoutesDescription = q.get_top_routes_info(conn)
       print(topUsers)
       print(topRoutes)
       print(topRoutesDescription)
       return render_template('rankings.html', topUsers = topUsers, topRoutes=topRoutes, topRoutesDescription=topRoutesDescription)

# Allows users to say which routes they have completed and give them a rating
# and a comment
@app.route('/submit_rating/', methods=["POST"])
def submit_rating():
    uid = session.get('uid')
    if uid is None:
        return redirect(url_for('intro'))

    # Get the form data: route ID, rating, and optional comment
    routeID = request.form.get('route_ID')
    rating = request.form.get('rating')
    comment = request.form.get('comment')

    # Validate the inputs
    if not routeID or not rating:
        flash('Route ID and rating are required.')
        return redirect(url_for('search_route'))

    try:
        routeID = int(routeID)
        rating = int(rating)
    except ValueError:
        flash('Invalid route ID or rating.')
        return redirect(url_for('search_route'))

    # Connect to the database
    conn = dbi.connect()
    with conn.cursor() as curs:
        # Insert the rating and comment into the route_rating table
        query_rating = '''
            INSERT INTO route_rating (uid, routeID, rating, comment) 
            VALUES (%s, %s, %s, %s)
        '''
        curs.execute(query_rating, (uid, routeID, rating, comment))

        # Optionally update user mileage (if necessary)
        query_findMileage = 'SELECT mileage FROM route_info WHERE routeID = %s'
        curs.execute(query_findMileage, (routeID,))
        row = curs.fetchone()
        if row:
            routeMileage = row[0]

            # Get the user's current mileage
            query_currentMileage = 'SELECT overall_mileage FROM user WHERE uid = %s'
            curs.execute(query_currentMileage, (uid,))
            row1 = curs.fetchone()
            if row1:
                currentM = float(row1[0])
                newMileage = currentM + routeMileage

                # Update the user's total mileage
                query_newMileage = 'UPDATE user SET overall_mileage = %s WHERE uid = %s'
                curs.execute(query_newMileage, (newMileage, uid))

        conn.commit()

    flash('Your rating and comment have been submitted. Thank you!')
    return redirect(url_for('search_route'))  # Redirect back to the route search page


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
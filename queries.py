import cs304dbi as dbi

def get_all_routes(conn):
    """
    Retrieves all route information from the database, including the username of the user who added each route.
    Returns:
        A list of tuples, where each tuple represents a route and includes all fields from 
        `route_info` and the `username` from the `user` table.
    """
    curs = dbi.dict_cursor(conn)
    sql = '''select routeID, route_info.created_at, name, route_description, route_tcx, 
    embedded_map_link, route_info.level, mileage, starting_location, starting_town, finishing_location, 
    out_and_back, bathroom, bathroom_description, water_fountain, fountain_description, addedBy, 
    uid, username, pronouns, user.level, overall_mileage, average_pace, routes_created,
    user.username from route_info inner join user on route_info.addedBy = user.uid'''
    curs.execute(sql)
    rows = curs.fetchall()
    return rows

def get_all_ratings(conn):
    """
    Retrieves all route ratings from the database, including the rating score out of 5 and the comment.
    Returns:
        A list of tuples, where each tuple represents all route ratings.
    """
    curs = dbi.cursor(conn)
    sql = '''select ratingID, uid, routeID, rating, comment from route_rating'''
    curs.execute(sql)
    rows = curs.fetchall()
    return rows

def get_avg_rating(conn):
    """
    Retrieves overall average route rating using the database.
    Returns:
        A list of tuples, where each tuple represents a route and includes the average rating of the route
    """
    curs = dbi.cursor(conn)
    sql = '''select distinct routeID, round(avg(rating), 1) from route_rating group by ratingID'''
    curs.execute(sql)
    rows = curs.fetchall()
    return rows


def get_user_routes(conn, user_id):
    """
    Retrieves all routes added by a specific user, including the username of the user.
    Collects the user_id that will be retrieved
    Returns:
        A list of tuples, where each tuple represents a route added by the specified user
        and includes all fields from `route_info` and the `username` from the `user` table.
    """
    curs = dbi.dict_cursor(conn)
    sql = '''select routeID, name, route_info.created_at, route_description, route_tcx, 
    embedded_map_link, route_info.level, mileage, starting_location, starting_town, finishing_location, 
    out_and_back, bathroom, bathroom_description, water_fountain, fountain_description, addedBy, 
    uid, username, pronouns, user.level, overall_mileage, average_pace, routes_created,
    user.username from route_info inner join user on route_info.addedBy = user.uid where addedBy = %s'''
    curs.execute(sql, [user_id])
    rows = curs.fetchall()
    return rows

def get_routes(conn, name, level, mileage, start, finish, out, bath, water):
    """
    Retrieves routes that match specified filters.
    Returns:
        A list of tuples, where each tuple represents a route that matches the filters.
    """
    curs = dbi.cursor(conn)
    sql = '''select routeID, name, route_description, route_tcx, 
    embedded_map_link, level, mileage, starting_location, starting_town, finishing_location, 
    out_and_back, bathroom, bathroom_description, water_fountain, fountain_description, addedBy from route_info 
    where '''
    filters = []
    if name != None:
        sql += 'name like %s and '
        filters.append('%'+ name + '%')
        print(name)
    if level != 'Any':
        sql += 'level like %s and '
        filters.append(level)
    if mileage != 25:
        sql += 'mileage <= %s and '
        filters.append(mileage)
    if start != 'Any':
        sql += 'starting_town like %s and '
        filters.append(start)
    if finish != 'Any':
        sql += 'finishing_town like %s and '
        filters.append(finish)
    if out != 'n/a':
        sql += 'out_and_back like %s and '
        filters.append(out)
    if bath != 'n/a':
        sql += 'bathroom like %s and '
        filters.append(bath)
    if water != 'n/a':
        sql += 'water_fountain like %s and '
        filters.append(water)
    print('before:' + sql)
    sql = sql.removesuffix('and ')
    print('after:' + sql)
    curs.execute(sql,filters)
    
    info = curs.fetchall()
    return info


def get_top_routes(conn):
    """
    Retrieves routes with the top three highest ratings.
    Returns:
        A list of tuples, where each tuple represents a route is in the top three highest rated routes.
    """
    sql = '''select routeID, avg(rating) as avg_rating from route_rating group by routeID order by avg_rating desc limit 3;'''
    curs = dbi.cursor(conn)
    curs.execute(sql)
    rows = curs.fetchall()
    return rows

def get_top_users(conn):
    """
    Retrieves three of the top users with the most amount of routes uploaded.
    Returns:
        A list of tuples, where each tuple represents a user is in the top three users.
    """
    sql = "select uid, username, pronouns, level, routes_created from user order by routes_created desc limit 3"
    curs = dbi.cursor(conn)
    curs.execute(sql)
    rows = curs.fetchall()
    return rows
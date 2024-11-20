import cs304dbi as dbi

def get_all_routes(conn):
    curs = dbi.cursor(conn)
    sql = '''select *, user.username from route_info inner join user on route_info.addedBy = user.uid'''
    curs.execute(sql)
    rows = curs.fetchall()
    return rows

def get_user_routes(conn, user_id):
    curs = dbi.cursor(conn)
    sql = '''select *, user.username from route_info inner join user on route_info.addedBy = user.uid where addedBy = %s'''
    curs.execute(sql, [user_id])
    rows = curs.fetchall()
    return rows

def get_routes(conn, name, level, mileage, start, finish, out, bath, water):
    curs = dbi.cursor(conn)
    sql = '''select * from route_info 
                where
                '''
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
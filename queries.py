import cs304dbi as dbi

def get_all_routes(conn):
    curs = dbi.cursor(conn)
    curs.execute('''select *, user.username from route_info inner join user on route_info.addedBy = user.uid''')
    rows = curs.fetchall()
    return rows
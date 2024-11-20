use routesct_db;

-- populating the user table
insert into user(username, password, pronouns, level, overall_mileage, average_pace, routes_created) 
values ('mhansen', 'iheartroutescout', 'she/her', 'Beginner', 0, 0840, 0);

insert into user(username, password, pronouns, level, overall_mileage, average_pace, routes_created) 
values ('nsobski', 'helloroutescout', 'she/her', 'Intermediate', 0, 0830, 1);

insert into user (username, password, pronouns, level, overall_mileage, average_pace, routes_created) 
values ('mluheda', 'r0ute$cout!', 'she/her', 'Intermediate', 0, 0930, 0);

insert into user (username, password, pronouns, level, overall_mileage, average_pace, routes_created) 
values ('yparedes', 'rootscoot!', 'she/her', 'Beginner', 0, 1500, 0);

-- populating the route_info table
insert into route_info(name, route_description, route_tcx, level, mileage, starting_location, starting_town,
finishing_location, finishing_town, out_and_back, bathroom, bathroom_description, water_fountain, fountain_description,
addedBy) values ('First Route', 'Run like your life depends on it on our first ever recorded route!', 'first_run.gpx',
'Beginner', 0, point(42.28929, 71.31742), 'Wellesley', point(42.29220, 71.30742), 'Wellesley', 'yes', 'yes', 'Wellesley Campus Center',
'yes', 'Wellesley Campus Center', 8);

insert into route_info(name, route_description, route_tcx, level, mileage, starting_location, starting_town,
finishing_location, finishing_town, out_and_back, bathroom, bathroom_description, water_fountain, fountain_description,
addedBy) values ('Bread and Butter', 'I love Pond Road', 'pond_rd_loop.gpx', 'Intermediate', 3, point(42.28929, 71.31742), 'Wellesley', 
point(42.29220, 71.30742), 'Wellesley', 'yes', 'no', 'None','no', 'None', 9);
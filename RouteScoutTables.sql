--Creates tables for RouteScout database

drop table if exists route_info;
drop table if exists routes_ran;
drop table if exists user;
drop table if exists route_rating;

create table user (
    uid integer auto_increment,
    created_at timestamp,
    username varchar(50),
    pronouns varchar(20),
    level enum('Beginner', 'Intermediate', 'Advanced'),
    overall_mileage integer,
    average_pace time,
    routes_created integer,
    primary key(uid)
);

create table route_info (
    routeID integer auto_increment,
    created_at timestamp,
    name varchar(60),
    route_description varchar(300),
    route_tcx text,
    level enum('Beginner', 'Intermediate', 'Advanced'),
    mileage float,
    starting_location point,
    starting_town enum('Newton', 'Cambridge', 'Wellesley', 'Boston', 'Framingham', 'Natick', 'Waltham', 'Somerville', 'Brookline', 'Medford', 'Malden', 'Revere'),
    finishing_location point,
    finishing_town enum('Newton', 'Cambridge', 'Wellesley', 'Boston', 'Framingham', 'Natick', 'Waltham', 'Somerville', 'Brookline', 'Medford', 'Malden', 'Revere'),
    out_and_back enum('yes', 'no'),
    bathroom enum('yes', 'no'),
    bathroom_description point,
    water_fountain enum('yes','no'),
    fountain_description point,
    addedBy integer,
    primary key(routeID),
    foreign key (addedBy) references user(uid) ON DELETE CASCADE
);

create table routes_ran (
    routeID integer,
    uid integer,
    primary key(routeID, uid),
    foreign key (uid) references user(uid) ON DELETE CASCADE,
    foreign key (routeID) references route_info(routeID) ON DELETE CASCADE
);

create table route_rating (
    ratingID integer auto_increment,
    uid integer,
    routeID integer,
    rating integer,
    comment text,
    primary key (ratingID),
    foreign key (routeID) references route_info(routeID) ON DELETE CASCADE,
    foreign key (uid) references user(uid) ON DELETE CASCADE
);
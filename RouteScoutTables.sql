--Creates tables for RouteScout database

drop table if exists route_info;
drop table if exists routes_ran;
drop table if exists user;
drop table if exists route_rating;

create table user (
    uid integer primary key,
    created_at timestamp,
    username varchar(50),
    pronouns varchar(20),
    level enum('Beginner', 'Intermediate', 'Advanced'),
    overall_mileage integer,
    average_pace time,
    routes_created integer
);

create table route_info (
    routeID integer primary key,
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
    foreign key (addedBy) references user(uid)
);

create table routes_ran (
    routeID integer,
    uid integer,
    primary key(routeID, uid),
    foreign key (uid) references user(uid),
    foreign key (routeID) references route_info(routeID)
);

create table route_rating (
    ratingID integer primary key,
    uid integer,
    routeID integer,
    rating integer,
    comment text,
    foreign key (routeID) references route_info(routeID),
    foreign key (uid) references user(uid)
);
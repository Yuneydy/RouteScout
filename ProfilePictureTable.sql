drop table if exists profilepictures;

create table profilepictures (
    uid integer not null,
    profilefilename varchar(50),
    primary key (uid),
    foreign key (uid) references user(uid) 
        on delete cascade on update cascade
);

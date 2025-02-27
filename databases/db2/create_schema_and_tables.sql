create schema demo;

create table demo.citizens (id integer primary key not null, ssn char(14) UNIQUE NOT null,firstname varchar(20),lastname varchar(64),birthdate date); 


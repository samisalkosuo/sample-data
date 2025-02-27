CREATE DATABASE demo;
GO
USE demo;
GO
CREATE TABLE addresses (id int primary key not null, address nvarchar(64), postalnumber char(10),municipality nvarchar(64));
CREATE TABLE professions (id int primary key not null, profession nvarchar(96));
GO
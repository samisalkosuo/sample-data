CREATE DATABASE demo;
GO
USE demo;
GO
CREATE TABLE Addresses (ID char(17) unique not null, address nvarchar(64), postalNumber char(10),municipality nvarchar(64));
CREATE TABLE Professions (ID char(17) unique not null, profession nvarchar(96));
GO
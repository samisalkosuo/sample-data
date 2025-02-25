#!/bin/bash
set -e
export DEMO_USER_PASSWORD=$POSTGRES_PASSWORD
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	-- Create user and table 
    CREATE USER $DEMO_USER_NAME;
    ALTER USER $DEMO_USER_NAME WITH PASSWORD '$DEMO_USER_PASSWORD';
	CREATE DATABASE $DEMO_DB_NAME;
	GRANT ALL PRIVILEGES ON DATABASE $DEMO_DB_NAME TO $DEMO_USER_NAME;
    \c $DEMO_DB_NAME;
    -- Create table and add privileges to user
    CREATE TABLE calldetailrecord (id serial PRIMARY KEY, anumber TEXT NOT NULL, bnumber TEXT NOT NULL, starttime TIMESTAMP NOT NULL, endtime TIMESTAMP NOT NULL, duration INTEGER NOT NULL);
    GRANT ALL PRIVILEGES ON SCHEMA public TO $DEMO_USER_NAME;
    GRANT ALL PRIVILEGES ON TABLE calldetailrecord TO $DEMO_USER_NAME;

    -- Grants USAGE (which includes SELECT) on all schemas.
    -- Grants SELECT on all tables, views, and sequences.  
    GRANT pg_read_all_data TO $DEMO_USER_NAME;

    -- Grants USAGE on all schemas.
    -- Grants INSERT, UPDATE, DELETE on all tables, views, and sequences.
    GRANT pg_write_all_data TO $DEMO_USER_NAME;
EOSQL

#!/bin/bash


source ${SETUPDIR?}/include/db2_constants
source ${SETUPDIR?}/include/db2_common_functions

csvFile=/tmp/db2-citizens.csv

create_demo_schema_and_tables()
{
    echo "(*) Creating demo schema and tables..."
    su - ${DB2INSTANCE?} -c "db2 connect to ${DBNAME?} && \
    db2 -tvmf /tmp/create_schema_and_tables.sql |tee /tmp/create_schema_and_tables.sql.out && \
    db2 connect reset"
    echo "(*) Creating demo schema and tables...done."
}

insert_citizens()
{
    echo "(*) Inserting citizens..."
    su - ${DB2INSTANCE?} -c "db2 connect to ${DBNAME?} && \
    db2 load from ${csvFile} of del replace into demo.citizens && \
    db2 connect reset"
    #db2-tvmf for debugging
    #db2 -tf /tmp/insert_citizens.sql > /tmp/insert_citizens.sql.out && \
    echo "(*) Inserting citizens...done."
}

create_demo_schema_and_tables
insert_citizens

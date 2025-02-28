#!/bin/bash

function log
{
    local msg=$1
    if [[ "${LOG}" == "true" ]]; then
        echo $msg
    fi
}

function createInsertCDRSQL
{        
    cd calldetailrecords
    #get random number of CDR insert SQLs...
    python3 create-insert-cdr-sql.py -1 > insert_cdr.sql
    local SQL_LINES=$(cat insert_cdr.sql |wc | awk '{print $1}')
    #cat insert_cdr.sql | awk '{print}' ORS=' '
    #echo $SQL_LINES
    local SQL=$(cat insert_cdr.sql | awk '{print}' ORS=' ')
    #insert to Postgres
    log "Inserting ${SQL_LINES} call detail records to CDR database..."
    echo | awk -v SQL="$SQL" -v CDR_DB_JDBC_URL="$CDR_DB_JDBC_URL" -v CDR_DB_USER_NAME="$CDR_DB_USER_NAME" -v CDR_DB_USER_PASSWORD="$CDR_DB_USER_PASSWORD" '{print "java -jar /datagenerator/jsql.jar -j " CDR_DB_JDBC_URL " -u " CDR_DB_USER_NAME " -p " CDR_DB_USER_PASSWORD " -s \"" SQL "\""}' | sh
    
    cd ..
}

while true; 
do 
    #create sample data
    createInsertCDRSQL

    sleep 1;
done


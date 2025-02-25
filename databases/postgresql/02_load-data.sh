#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DEMO_DB_NAME" <<-EOSQL    
    COPY calldetailrecord FROM '/tmp/calldetailrecords.csv' WITH CSV HEADER;
EOSQL

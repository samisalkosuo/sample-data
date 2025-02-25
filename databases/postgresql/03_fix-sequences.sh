#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    \c $DEMO_DB_NAME;
    -- fix sequence
    select setval('calldetailrecord_id_seq', (select max(id)  from calldetailrecord)); 
EOSQL



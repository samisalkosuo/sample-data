#!/bin/bash
csvFile=/tmp/oracle-phonenumbers.csv

cat << EOF > /opt/oracle/scripts/startup/02_create_user.sql
alter session set "_ORACLE_SCRIPT"=true;
create user ${ORACLE_USER} identified by ${ORACLE_PWD};
grant dba to ${ORACLE_USER};
EOF

cat << EOF > /opt/oracle/scripts/startup/03_create-table.sql
create table ${ORACLE_USER}.phonenumbers (id char(17) unique not null, phonenumber char(12));
EOF

cat << EOF > /opt/oracle/scripts/startup/04-insert-data.sh
#!/bin/sh
sqlldr userid=${ORACLE_USER}/${ORACLE_PWD} data=${csvFile} control=/opt/oracle/scripts/startup/load-phonenumbers.ctl
EOF


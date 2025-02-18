FROM container-registry.oracle.com/database/free:latest

#default env vars
ENV ORACLE_CHARACTERSET=AL32UTF8
ENV ORACLE_PWD=passw0rd

#user and schema name
ENV ORACLE_USER=demo

USER root
COPY *.sh /opt/oracle/scripts/startup
RUN chmod 777 /opt/oracle/scripts/startup/*sh
COPY *.sql /opt/oracle/scripts/startup
RUN chmod 777 /opt/oracle/scripts/startup/*sql

#phonenumbers
COPY oracle-phonenumbers.csv.gz /tmp/
RUN cd /tmp && gunzip oracle-phonenumbers.csv.gz
RUN chmod 777 /tmp/*csv

USER oracle

COPY load-phonenumbers.ctl /opt/oracle/scripts/startup



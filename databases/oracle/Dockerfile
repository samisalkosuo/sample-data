FROM container-registry.oracle.com/database/free:latest

#default env vars
ENV ORACLE_CHARACTERSET=AL32UTF8
ENV ORACLE_PWD=passw0rd

#user and schema name
ENV ORACLE_USER=demo

USER root
COPY *.sh /opt/oracle/scripts/startup
RUN chmod a+x /opt/oracle/scripts/startup/*sh
USER oracle

COPY *.sql /opt/oracle/scripts/startup

#phonenumbers
COPY phonenumbers.zip /tmp/
RUN cd /tmp && unzip phonenumbers.zip
RUN chmod a+x /tmp/*csv
COPY load-phonenumbers.ctl /opt/oracle/scripts/startup




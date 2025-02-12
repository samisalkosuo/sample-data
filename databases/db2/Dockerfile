FROM icr.io/db2_community/db2

#default environment variables
ENV LICENSE=accept
ENV DB2INSTANCE=db2inst1
ENV DB2INST1_PASSWORD=passw0rd
ENV DBNAME=demodb
ENV BLU=false
ENV ENABLE_ORACLE_COMPATIBILITY=false
ENV UPDATEAVAIL=NO
ENV TO_CREATE_SAMPLEDB=false
ENV REPODB=true
ENV IS_OSXFS=false
ENV PERSISTENT_HOME=false
ENV HADR_ENABLED=false

#copy files to tmp
COPY create_schema_and_tables.sql /tmp/
RUN chmod a+x /tmp/create_schema_and_tables.sql
COPY citizens.zip /tmp/
RUN cd /tmp && unzip citizens.zip
RUN chmod a+x /tmp/*csv

#copy script files
RUN mkdir /var/custom
COPY create_citizens_database.sh /var/custom
RUN chmod a+x /var/custom/create_citizens_database.sh

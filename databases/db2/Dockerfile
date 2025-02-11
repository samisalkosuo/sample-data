FROM icr.io/db2_community/db2

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

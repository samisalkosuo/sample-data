FROM docker.io/kazhar/jsql:latest as build

FROM docker.io/kazhar/devcon:latest

WORKDIR /datagenerator

RUN devcon-tool install-java

USER root

#copy jsql
COPY --from=build /jsql/jsql-1.0-SNAPSHOT-jar-with-dependencies.jar ./jsql.jar

#copy data
COPY data/*gz ./data/
#extract data
RUN cd data && gunzip *gz

COPY calldetailrecords/ ./calldetailrecords/

#copy scripts
COPY scripts/ .

#change owner
RUN chmod 755 *sh && \
    chown -R devcon:devcon /datagenerator/

USER devcon

#environment variables
ENV CDR_DB_JDBC_URL=jdbc:postgresql://postgresql:5432/demo
ENV CDR_DB_USER_NAME=demo
ENV CDR_DB_USER_PASSWORD=passw0rd
ENV LOG=true

ENTRYPOINT /bin/bash ./start-generator.sh
#CMD ["/usr/bin/bash"]

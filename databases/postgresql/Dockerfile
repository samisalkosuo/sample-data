FROM postgres:17.4-alpine3.21

ENV POSTGRES_PASSWORD=passw0rd
ENV POSTGRES_USER=postgres
ENV POSTGRES_DB=postgres

#demo user and database, password is POSTGRES_PASSWORD
ENV DEMO_USER_NAME=demo
ENV DEMO_DB_NAME=demo

EXPOSE 5432

COPY calldetailrecords.csv.gz /tmp/

RUN cd /tmp && gunzip calldetailrecords.csv.gz

COPY *sh /docker-entrypoint-initdb.d/


FROM mcr.microsoft.com/mssql/server:2022-latest

ENV ACCEPT_EULA=Y
ENV MSSQL_SA_PASSWORD="MySTr0ng@Passw0rd"

WORKDIR /sqlserver

USER root

#RUN apt -y install zip

COPY *.sh .
COPY *.sql .
COPY *.gz .
RUN gunzip sqlserver-addresses.csv.gz && \
    gunzip sqlserver-professions.csv.gz && \
    chmod 777 /sqlserver/*.csv && \
    chmod 777 /sqlserver/*.sh && \
    chmod 777 /sqlserver/*.sql

USER mssql
ENTRYPOINT /bin/bash ./entrypoint.sh
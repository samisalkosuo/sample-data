FROM postgres:17.4-alpine3.21 AS builder

#https://github.com/eulerto/wal2json/issues/68#issuecomment-529136552
RUN apk add --no-cache build-base git
RUN git clone https://github.com/eulerto/wal2json.git
WORKDIR /wal2json
#RUN USE_PGXS=1 make && make install
RUN make with_llvm=no && make with_llvm=no install


FROM postgres:17.4-alpine3.21

COPY --from=builder /wal2json/wal2json.so /usr/local/lib/postgresql/

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


FROM mongo:7.0.20-jammy

ARG MONGODB_USER
ARG MONGODB_PASS
ENV MONGO_INITDB_ROOT_USERNAME=${MONGODB_USER}
ENV MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PASS}

COPY repository/infra/mongodb/init/ /docker-entrypoint-initdb.d/

WORKDIR /data/db

CMD ["mongod"]
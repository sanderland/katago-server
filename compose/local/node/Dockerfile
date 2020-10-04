FROM node:10-stretch-slim

WORKDIR /app

COPY ./src/frontend/package.json /app
COPY ./src/frontend/yarn.lock /app

RUN apt-get update && apt-get install -y autoconf && apt-get install -y build-essential
RUN yarn && yarn cache clean

ENV PATH ./node_modules/.bin/:$PATH

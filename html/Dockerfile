FROM docker.io/node:latest
RUN mkdir /app
WORKDIR /app
COPY ./app/* /app/
RUN cd /app && npm init -y
COPY ./package.json.dist /app/package.json
RUN npm install @azure/storage-blob parcel && npm install -g parcel-bundler
CMD ["npm", "start"]

FROM node:24-slim

WORKDIR /app

COPY package.json yarn.lock ./

RUN yarn install

COPY . .

EXPOSE 8100

CMD ["node", "server.js"]

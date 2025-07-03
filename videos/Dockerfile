FROM node:24-slim

WORKDIR /usr/src/app

COPY package.json yarn.lock* ./

RUN yarn install --production --frozen-lockfile || yarn install --production

COPY . .

EXPOSE ${PORT:-8000}

CMD ["yarn", "start"]

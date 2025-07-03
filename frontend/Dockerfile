FROM node:24-slim AS builder

WORKDIR /app

ENV NODE_ENV=production

COPY package.json yarn.lock ./

# Install dependencies using yarn
# (Make sure your packageManager in package.json matches your lock file or use the correct command)
RUN yarn install --frozen-lockfile --production=false

COPY . .

RUN yarn build

FROM node:24-slim

WORKDIR /app

COPY --from=builder /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]

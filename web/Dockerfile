# Build frontend, output to /dist for Caddy to serve
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Minimal image that copies built files to volume on start
FROM alpine:latest
COPY --from=builder /app/dist /app/dist
VOLUME /dist
CMD ["sh", "-c", "rm -rf /dist/* && cp -r /app/dist/* /dist/ && echo 'Static files copied to /dist'"]

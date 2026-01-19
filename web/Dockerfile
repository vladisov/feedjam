# Build frontend, output to /dist for Caddy to serve
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Minimal image just to hold the built files
FROM alpine:latest
COPY --from=builder /app/dist /dist

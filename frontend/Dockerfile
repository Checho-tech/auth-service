# syntax=docker/dockerfile:1

# ---- Build stage ----
FROM node:22-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite env vars are baked in at BUILD time, not read at container startup —
# unlike the backend's runtime .env. The browser (not this container) is
# what calls the API, so this must be an address reachable from the host
# machine (localhost:8000, since docker-compose publishes that port),
# never the internal Docker network hostname ("app").
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


# ---- Runtime stage: static files behind a minimal Nginx ----
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost/ || exit 1

# --- сборка ---
FROM node:22-alpine AS build
WORKDIR /app

# сначала только зависимости: слой кешируется, пока не меняется package-lock.json
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- раздача статики ---
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
# скрипты из /docker-entrypoint.d/ образ nginx выполняет перед запуском сервера
COPY docker-entrypoint.d/40-app-config.sh /docker-entrypoint.d/40-app-config.sh
RUN chmod +x /docker-entrypoint.d/40-app-config.sh

EXPOSE 80

FROM node:22-bookworm-slim

# без UTF-8 локали Chromium в Linux теряет кириллические имена скачиваемых файлов
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /e2e
COPY package.json package-lock.json ./
RUN npm ci \
    # только Chromium с системными зависимостями — образ заметно меньше полного образа Playwright
    && npx playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*
COPY . .

CMD ["npx", "playwright", "test"]

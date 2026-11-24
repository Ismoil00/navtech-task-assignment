// Адрес API читается во время работы, а не при сборке: один и тот же образ
// фронтенда можно запускать с любым backend, поменяв только переменную окружения.
export const config = {
  apiUrl: window.__APP_CONFIG__?.apiUrl ?? 'http://localhost:8000/api',
};

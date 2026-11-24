/// <reference types="vite/client" />

interface Window {
  /** Настройки, которые подставляются при старте контейнера (public/config.js). */
  __APP_CONFIG__?: { apiUrl?: string };
}

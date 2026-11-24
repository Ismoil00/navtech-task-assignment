import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { config } from '../config';
import type { TokenResponse } from './types';

/**
 * HTTP-клиент приложения.
 *
 * Access-токен живёт только в памяти (Redux), refresh-токен — в httpOnly cookie,
 * которую JavaScript не видит. Когда access-токен истекает, сервер отвечает 401:
 * клиент один раз обновляет сессию и повторяет исходный запрос.
 */
export const http = axios.create({
  baseURL: config.apiUrl,
  // браузер отправит cookie с refresh-токеном (backend на другом порту — нужен CORS)
  withCredentials: true,
});

interface SessionBridge {
  getAccessToken: () => string | null;
  onRefreshed: (tokens: TokenResponse) => void;
  onSessionLost: () => void;
}

// Связь со store задаётся при его создании — так нет циклического импорта
let session: SessionBridge = {
  getAccessToken: () => null,
  onRefreshed: () => undefined,
  onSessionLost: () => undefined,
};

export function connectSession(bridge: SessionBridge): void {
  session = bridge;
}

http.interceptors.request.use((request) => {
  const token = session.getAccessToken();
  if (token) request.headers.Authorization = `Bearer ${token}`;
  return request;
});

let refreshInFlight: Promise<string | null> | null = null;

/**
 * Обновляет access-токен. Параллельные вызовы получают один и тот же запрос:
 * если одновременно истекли пять запросов, на сервер уйдёт одно обновление.
 */
export function refreshAccessToken(): Promise<string | null> {
  refreshInFlight ??= requestNewToken().finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

async function requestNewToken(): Promise<string | null> {
  for (let attempt = 1; attempt <= 2; attempt += 1) {
    try {
      const { data } = await axios.post<TokenResponse>(`${config.apiUrl}/auth/refresh`, null, {
        withCredentials: true,
      });
      session.onRefreshed(data);
      return data.access_token;
    } catch (error) {
      const code = (error as AxiosError<{ error?: { code?: string } }>).response?.data?.error?.code;
      // сессию только что обновила соседняя вкладка — cookie уже новая, пробуем ещё раз
      if (code === 'REFRESH_TOKEN_ROTATED' && attempt === 1) continue;
      session.onSessionLost();
      return null;
    }
  }
  return null;
}

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean };

http.interceptors.response.use(undefined, async (error: AxiosError) => {
  const original = error.config as RetriableConfig | undefined;
  const isAuthCall = original?.url?.startsWith('/auth/');
  if (error.response?.status === 401 && original && !original._retried && !isAuthCall) {
    original._retried = true;
    const token = await refreshAccessToken();
    if (token) {
      original.headers.Authorization = `Bearer ${token}`;
      return http(original);
    }
  }
  return Promise.reject(error);
});

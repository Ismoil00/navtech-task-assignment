import { type BaseQueryFn, createApi } from '@reduxjs/toolkit/query/react';
import type { Method } from 'axios';

import { type ApiError, toApiError } from './errors';
import { http } from './http';

export interface HttpArgs {
  url: string;
  method?: Method;
  data?: unknown;
  params?: Record<string, unknown>;
  headers?: Record<string, string>;
}

// RTK Query ходит в API через тот же axios-клиент: с токеном и его обновлением
const axiosBaseQuery: BaseQueryFn<HttpArgs, unknown, ApiError> = async (args) => {
  try {
    const response = await http.request({
      url: args.url,
      method: args.method ?? 'GET',
      data: args.data,
      params: args.params,
      headers: args.headers,
    });
    return { data: response.data };
  } catch (error) {
    return { error: toApiError(error) };
  }
};

/**
 * Опции для запросов заявок. Статус меняет и другая сторона (оператор или заявитель),
 * поэтому при открытии страницы и возврате на вкладку данные берутся с сервера,
 * а не из кеша. Справочник услуг их не использует: он грузится один раз при входе.
 */
export const ALWAYS_FRESH = { refetchOnMountOrArgChange: true, refetchOnFocus: true } as const;

/** Общий API-слайс. Эндпоинты добавляются в файлах разделов через injectEndpoints. */
export const api = createApi({
  reducerPath: 'api',
  baseQuery: axiosBaseQuery,
  tagTypes: ['Application', 'MyApplications', 'Queue', 'ServiceTypes'],
  endpoints: () => ({}),
});

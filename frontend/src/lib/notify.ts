import { notifications } from '@mantine/notifications';

import { type ApiError, isApiError } from '../api/errors';

export function notifySuccess(message: string, title?: string): void {
  notifications.show({ color: 'teal', title, message });
}

export function notifyError(error: unknown, fallback = 'Не удалось выполнить действие'): void {
  const message = isApiError(error) ? error.message : fallback;
  notifications.show({ color: 'red', title: 'Ошибка', message });
}

/** Ошибку RTK Query (unwrap) приводим к ApiError, чтобы прочитать код. */
export function asApiError(error: unknown): ApiError | null {
  return isApiError(error) ? error : null;
}

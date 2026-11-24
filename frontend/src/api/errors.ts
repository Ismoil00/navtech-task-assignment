import axios from 'axios';

/** Ошибка API в едином виде. code — машинный код backend, message — текст для пользователя. */
export interface ApiError {
  status: number | 'NETWORK' | 'TIMEOUT';
  code: string;
  message: string;
  details?: unknown;
}

interface ErrorBody {
  error?: { code?: string; message?: string; details?: unknown };
}

export function toApiError(error: unknown): ApiError {
  if (!axios.isAxiosError(error)) {
    return { status: 'NETWORK', code: 'UNKNOWN', message: 'Что-то пошло не так. Попробуйте ещё раз' };
  }
  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
    return { status: 'TIMEOUT', code: 'TIMEOUT', message: 'Сервер не ответил вовремя' };
  }
  if (!error.response) {
    return {
      status: 'NETWORK',
      code: 'NETWORK_ERROR',
      message: 'Нет связи с сервером. Проверьте подключение',
    };
  }
  const body = (error.response.data as ErrorBody | undefined)?.error;
  return {
    status: error.response.status,
    code: body?.code ?? 'HTTP_ERROR',
    message: body?.message ?? 'Не удалось выполнить запрос',
    details: body?.details,
  };
}

export function isApiError(value: unknown): value is ApiError {
  return typeof value === 'object' && value !== null && 'code' in value && 'message' in value;
}

/** Ошибки полей из ответа 422: { full_name: "...", phone: "..." }. */
export function fieldErrors(error: ApiError): Record<string, string> {
  if (!Array.isArray(error.details)) return {};
  const result: Record<string, string> = {};
  for (const item of error.details as Array<{ field?: string | null; message?: string }>) {
    if (item.field && item.message && !(item.field in result)) {
      result[item.field] = item.message;
    }
  }
  return result;
}

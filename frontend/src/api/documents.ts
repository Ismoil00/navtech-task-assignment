import axios from 'axios';

import { type ApiError, toApiError } from './errors';
import { http } from './http';
import type { Application } from './types';

/** Загрузка документа с прогрессом. Возвращает обновлённую заявку. */
export async function uploadDocument(
  applicationId: string,
  file: File,
  onProgress: (percent: number) => void,
): Promise<Application> {
  const body = new FormData();
  body.append('file', file);
  try {
    const { data } = await http.put<Application>(`/applications/${applicationId}/file`, body, {
      onUploadProgress: (event) => {
        if (event.total) onProgress(Math.round((event.loaded / event.total) * 100));
      },
    });
    return data;
  } catch (error) {
    throw toApiError(error);
  }
}

/**
 * Получает файл запросом с токеном. Обычная ссылка <a href> не подошла бы:
 * браузер не добавит к ней заголовок Authorization.
 */
async function fetchDocument(url: string): Promise<{ blob: Blob; filename: string }> {
  try {
    const response = await http.get<Blob>(url, { responseType: 'blob' });
    const disposition = String(response.headers['content-disposition'] ?? '');
    return { blob: response.data, filename: filenameFrom(disposition) };
  } catch (error) {
    throw await blobErrorToApiError(error);
  }
}

export async function downloadDocument(url: string): Promise<void> {
  const { blob, filename } = await fetchDocument(url);
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  // надёжнее для разных браузеров: ссылка находится в документе, а blob-адрес
  // освобождается не сразу, а когда загрузка уже точно началась
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(objectUrl), 10_000);
}

/** Открывает документ в новой вкладке (PDF и изображения браузер покажет сам). */
export async function openDocument(url: string): Promise<void> {
  // вкладку открываем сразу, в ответ на клик: иначе браузер посчитает её всплывающим окном
  const tab = window.open('', '_blank');
  try {
    const { blob } = await fetchDocument(url);
    const objectUrl = URL.createObjectURL(blob);
    if (tab) tab.location.href = objectUrl;
    setTimeout(() => URL.revokeObjectURL(objectUrl), 60_000);
  } catch (error) {
    tab?.close();
    throw error;
  }
}

function filenameFrom(disposition: string): string {
  // filename* (RFC 5987) содержит настоящее имя, в том числе кириллицей
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(disposition)?.[1];
  if (encoded) return decodeURIComponent(encoded);
  return /filename="([^"]+)"/i.exec(disposition)?.[1] ?? 'document';
}

// при responseType: 'blob' тело ошибки тоже приходит как Blob — разбираем JSON вручную
async function blobErrorToApiError(error: unknown): Promise<ApiError> {
  if (axios.isAxiosError(error) && error.response?.data instanceof Blob) {
    try {
      error.response.data = JSON.parse(await error.response.data.text());
    } catch {
      // не JSON — оставляем общее сообщение
    }
  }
  return toApiError(error);
}

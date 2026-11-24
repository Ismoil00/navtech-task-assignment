import { parsePhoneNumberFromString } from 'libphonenumber-js';

const dateTime = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium', timeStyle: 'short' });
const date = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'medium' });

export function formatDateTime(value: string | null | undefined): string {
  return value ? dateTime.format(new Date(value)) : '—';
}

export function formatDate(value: string | null | undefined): string {
  return value ? date.format(new Date(value)) : '—';
}

/** Сумма в минимальных единицах (дирамах) -> «120,00 TJS». */
export function formatMoney(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency }).format(amount / 100);
  } catch {
    return `${(amount / 100).toFixed(2)} ${currency}`;
  }
}

/** +992931234567 -> «+992 93 123 4567». */
export function formatPhone(value: string): string {
  return parsePhoneNumberFromString(value)?.formatInternational() ?? value;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
}

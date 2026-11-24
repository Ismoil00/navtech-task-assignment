import type { ApplicationStatus, PaymentStatus } from '../api/types';

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  draft: 'Черновик',
  paid: 'Оплачена',
  submitted: 'На рассмотрении',
  approved: 'Одобрена',
  rejected: 'Отклонена',
  returned: 'На доработке',
};

export const STATUS_COLORS: Record<ApplicationStatus, string> = {
  draft: 'gray',
  paid: 'blue',
  submitted: 'yellow',
  approved: 'teal',
  rejected: 'red',
  returned: 'orange',
};

/** Подсказка заявителю: что делать дальше. */
export const APPLICANT_NEXT_STEP: Record<ApplicationStatus, string> = {
  draft: 'Заполните, приложите документ и оплатите',
  paid: 'Оплачено — отправьте на рассмотрение',
  submitted: 'Ожидает решения оператора',
  approved: 'Заявка одобрена',
  rejected: 'Отклонена, оплата возвращена',
  returned: 'Исправьте и отправьте снова',
};

export const PAYMENT_LABELS: Record<PaymentStatus, string> = {
  processing: 'Обрабатывается',
  succeeded: 'Оплачено',
  failed: 'Не прошла',
  refunded: 'Возвращена',
};

export const PAYMENT_COLORS: Record<PaymentStatus, string> = {
  processing: 'yellow',
  succeeded: 'teal',
  failed: 'red',
  refunded: 'gray',
};

export const APPLICANT_STATUS_FILTER: ApplicationStatus[] = [
  'draft',
  'paid',
  'submitted',
  'returned',
  'approved',
  'rejected',
];

/** Оператор видит только отправленные заявки. */
export const OPERATOR_STATUS_FILTER: ApplicationStatus[] = [
  'submitted',
  'returned',
  'approved',
  'rejected',
];

// Типы ответов API. Поля названы так же, как в backend (snake_case), без преобразований.

export type UserRole = 'applicant' | 'operator';

export type ApplicationStatus =
  | 'draft'
  | 'paid'
  | 'submitted'
  | 'approved'
  | 'rejected'
  | 'returned';

export type PaymentStatus = 'processing' | 'succeeded' | 'failed' | 'refunded';

/** Что пользователь может сделать с заявкой прямо сейчас — решает сервер. */
export type AllowedAction =
  | 'edit'
  | 'upload_file'
  | 'delete'
  | 'pay'
  | 'submit'
  | 'approve'
  | 'reject'
  | 'return';

export type DecisionAction = 'approve' | 'reject' | 'return';

export interface User {
  id: string;
  username: string;
  full_name: string;
  role: UserRole;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
  user: User;
}

export interface ServiceType {
  id: number;
  code: string;
  name: string;
  description: string | null;
  price: number; // в дирамах
  currency: string;
}

export interface ServiceTypeBrief {
  id: number;
  name: string;
  price: number;
  currency: string;
}

export interface Attachment {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface Payment {
  id: string;
  status: PaymentStatus;
  amount: number;
  currency: string;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
  refunded_at: string | null;
}

export interface HistoryEntry {
  id: number;
  from_status: ApplicationStatus | null;
  to_status: ApplicationStatus;
  comment: string | null;
  created_at: string;
  actor: { full_name: string; role: UserRole };
}

export interface ApplicationListItem {
  id: string;
  status: ApplicationStatus;
  service_type: ServiceTypeBrief;
  full_name: string;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}

export interface Application extends ApplicationListItem {
  phone: string;
  comment: string | null;
  decided_at: string | null;
  attachment: Attachment | null;
  payment: Payment | null;
  history: HistoryEntry[];
  allowed_actions: AllowedAction[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApplicationInput {
  full_name: string;
  phone: string;
  service_type_id: number;
  comment: string | null;
}

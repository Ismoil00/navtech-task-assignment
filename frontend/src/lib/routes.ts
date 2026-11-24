import type { UserRole } from '../api/types';

export const routes = {
  login: '/login',
  myApplications: '/applications',
  newApplication: '/applications/new',
  myApplication: (id: string) => `/applications/${id}`,
  queue: '/operator/applications',
  review: (id: string) => `/operator/applications/${id}`,
};

/** Стартовая страница кабинета для роли. */
export function homePath(role: UserRole): string {
  return role === 'operator' ? routes.queue : routes.myApplications;
}

import { Navigate, Outlet, useLocation } from 'react-router';

import type { UserRole } from '../../api/types';
import { useAppSelector } from '../../app/hooks';
import { FullPageLoader } from '../../components/FullPageLoader';
import { homePath, routes } from '../../lib/routes';
import { selectSessionStatus, selectUser } from './authSlice';

/**
 * Пускает в раздел только пользователя нужной роли.
 * Это удобство интерфейса: настоящая проверка роли — на сервере.
 */
export function RequireRole({ role }: { role: UserRole }) {
  const status = useAppSelector(selectSessionStatus);
  const user = useAppSelector(selectUser);
  const location = useLocation();

  if (status === 'checking') return <FullPageLoader />;
  if (!user) return <Navigate to={routes.login} replace state={{ from: location.pathname }} />;
  if (user.role !== role) return <Navigate to={homePath(user.role)} replace />;
  return <Outlet />;
}

/** Корень сайта: отправляет в кабинет по роли или на вход. */
export function HomeRedirect() {
  const status = useAppSelector(selectSessionStatus);
  const user = useAppSelector(selectUser);

  if (status === 'checking') return <FullPageLoader />;
  return <Navigate to={user ? homePath(user.role) : routes.login} replace />;
}

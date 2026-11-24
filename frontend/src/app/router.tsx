import { Title } from '@mantine/core';
import { createBrowserRouter } from 'react-router';

import { AppLayout } from '../components/AppLayout';
import { NotFoundPage } from '../components/NotFoundPage';
import { LoginPage } from '../features/auth/LoginPage';
import { MyApplicationsPage } from '../features/applicant/MyApplicationsPage';
import { HomeRedirect, RequireRole } from '../features/auth/RequireRole';

function Placeholder({ title }: { title: string }) {
  return <Title order={2}>{title}</Title>;
}

export const router = createBrowserRouter([
  { path: '/', element: <HomeRedirect /> },
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireRole role="applicant" />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/applications', element: <MyApplicationsPage /> },
          { path: '/applications/new', element: <Placeholder title="Новая заявка" /> },
        ],
      },
    ],
  },
  {
    element: <RequireRole role="operator" />,
    children: [
      {
        element: <AppLayout />,
        children: [{ path: '/operator/applications', element: <Placeholder title="Очередь заявок" /> }],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
]);

import { Title } from '@mantine/core';
import { createBrowserRouter } from 'react-router';

import { AppLayout } from '../components/AppLayout';
import { NotFoundPage } from '../components/NotFoundPage';
import { LoginPage } from '../features/auth/LoginPage';
import { ApplicationPage } from '../features/applicant/ApplicationPage';
import { MyApplicationsPage } from '../features/applicant/MyApplicationsPage';
import { NewApplicationPage } from '../features/applicant/NewApplicationPage';
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
          { path: '/applications/new', element: <NewApplicationPage /> },
          { path: '/applications/:id', element: <ApplicationPage /> },
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

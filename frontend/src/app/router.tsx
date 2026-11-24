import { createBrowserRouter } from 'react-router';

import { AppLayout } from '../components/AppLayout';
import { NotFoundPage } from '../components/NotFoundPage';
import { ApplicationPage } from '../features/applicant/ApplicationPage';
import { MyApplicationsPage } from '../features/applicant/MyApplicationsPage';
import { NewApplicationPage } from '../features/applicant/NewApplicationPage';
import { LoginPage } from '../features/auth/LoginPage';
import { HomeRedirect, RequireRole } from '../features/auth/RequireRole';
import { QueuePage } from '../features/operator/QueuePage';
import { ReviewPage } from '../features/operator/ReviewPage';

export const router = createBrowserRouter([
  { path: '/', element: <HomeRedirect /> },
  { path: '/login', element: <LoginPage /> },
  {
    // кабинет заявителя
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
    // кабинет оператора
    element: <RequireRole role="operator" />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/operator/applications', element: <QueuePage /> },
          { path: '/operator/applications/:id', element: <ReviewPage /> },
        ],
      },
    ],
  },
  { path: '*', element: <NotFoundPage /> },
]);

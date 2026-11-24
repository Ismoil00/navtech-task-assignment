import { Center, Title } from '@mantine/core';
import { createBrowserRouter } from 'react-router';

import { HomeRedirect, RequireRole } from '../features/auth/RequireRole';

function Placeholder({ title }: { title: string }) {
  return (
    <Center h="100vh">
      <Title order={3}>{title}</Title>
    </Center>
  );
}

export const router = createBrowserRouter([
  { path: '/', element: <HomeRedirect /> },
  { path: '/login', element: <Placeholder title="Вход" /> },
  {
    element: <RequireRole role="applicant" />,
    children: [{ path: '/applications', element: <Placeholder title="Мои заявки" /> }],
  },
  {
    element: <RequireRole role="operator" />,
    children: [{ path: '/operator/applications', element: <Placeholder title="Очередь заявок" /> }],
  },
  { path: '*', element: <Placeholder title="Страница не найдена" /> },
]);

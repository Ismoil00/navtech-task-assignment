import { MantineProvider } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { useEffect } from 'react';
import { Provider } from 'react-redux';
import { RouterProvider } from 'react-router';

import { refreshAccessToken } from '../api/http';
import { router } from './router';
import { store } from './store';
import { theme } from './theme';

export function App() {
  useEffect(() => {
    // после перезагрузки страницы токена в памяти нет — восстанавливаем сессию по cookie
    if (store.getState().auth.status === 'checking') {
      void refreshAccessToken();
    }
  }, []);

  return (
    <Provider store={store}>
      <MantineProvider theme={theme} defaultColorScheme="light">
        <ModalsProvider>
          <Notifications position="top-right" />
          <RouterProvider router={router} />
        </ModalsProvider>
      </MantineProvider>
    </Provider>
  );
}

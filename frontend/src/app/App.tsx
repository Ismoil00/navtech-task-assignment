import { Center, MantineProvider, Stack, Text, Title } from '@mantine/core';
import { Notifications } from '@mantine/notifications';

import { theme } from './theme';

export function App() {
  return (
    <MantineProvider theme={theme} defaultColorScheme="light">
      <Notifications position="top-right" />
      <Center h="100vh">
        <Stack align="center" gap="xs">
          <Title order={2}>Сервис подачи заявок</Title>
          <Text c="dimmed">Интерфейс в разработке</Text>
        </Stack>
      </Center>
    </MantineProvider>
  );
}

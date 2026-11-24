import { Button, Center, Stack, Text, Title } from '@mantine/core';
import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <Center mih="60vh">
      <Stack align="center" gap="xs">
        <Title order={1} c="indigo.6">
          404
        </Title>
        <Text c="dimmed">Такой страницы нет или у вас нет к ней доступа</Text>
        <Button component={Link} to="/" variant="light" mt="sm">
          На главную
        </Button>
      </Stack>
    </Center>
  );
}

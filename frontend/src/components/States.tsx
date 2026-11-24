import { Alert, Button, Paper, Stack, Text, ThemeIcon, Title } from '@mantine/core';
import { IconAlertTriangle, IconInbox } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import { isApiError } from '../api/errors';

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Paper withBorder p="xl">
      <Stack align="center" gap="xs" py="lg">
        <ThemeIcon size={56} radius="xl" variant="light" color="indigo">
          <IconInbox size={30} />
        </ThemeIcon>
        <Title order={4} mt="sm">
          {title}
        </Title>
        {description && (
          <Text c="dimmed" size="sm" ta="center" maw={420}>
            {description}
          </Text>
        )}
        {action && <div style={{ marginTop: 8 }}>{action}</div>}
      </Stack>
    </Paper>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = isApiError(error) ? error.message : 'Не удалось загрузить данные';
  return (
    <Alert color="red" variant="light" icon={<IconAlertTriangle size={18} />} title="Ошибка">
      <Stack gap="sm" align="flex-start">
        <Text size="sm">{message}</Text>
        {onRetry && (
          <Button size="xs" variant="white" color="red" onClick={onRetry}>
            Повторить
          </Button>
        )}
      </Stack>
    </Alert>
  );
}

import { Button, Group, List, Paper, Text, ThemeIcon, Title } from '@mantine/core';
import { IconCheck, IconCircleDashed, IconSend } from '@tabler/icons-react';

import { useSubmitApplicationMutation } from '../../api/applicationsApi';
import type { Application } from '../../api/types';
import { notifyError, notifySuccess } from '../../lib/notify';

const BEFORE_SUBMISSION = new Set(['draft', 'paid', 'returned']);

export function SubmitSection({ application }: { application: Application }) {
  const [submit, { isLoading }] = useSubmitApplicationMutation();
  if (!BEFORE_SUBMISSION.has(application.status)) return null;

  const canSubmit = application.allowed_actions.includes('submit');
  const resubmit = application.status === 'returned';
  const paid = application.status !== 'draft';

  const handleSubmit = async () => {
    try {
      await submit(application.id).unwrap();
      notifySuccess('Заявка отправлена на рассмотрение');
    } catch (error) {
      notifyError(error);
    }
  };

  return (
    <Paper withBorder p="lg">
      <Title order={4} mb={4}>
        {resubmit ? 'Повторная отправка' : 'Отправка на рассмотрение'}
      </Title>
      <Text size="sm" c="dimmed" mb="md">
        {resubmit
          ? 'Исправьте то, что просил оператор, и отправьте заявку снова. Оплата уже учтена.'
          : 'После отправки изменить заявку будет нельзя, пока оператор не вернёт её на доработку.'}
      </Text>

      {!canSubmit && (
        <List spacing={6} size="sm" mb="md" center>
          <Requirement done={application.attachment !== null}>Приложен документ</Requirement>
          <Requirement done={paid}>Заявка оплачена</Requirement>
        </List>
      )}

      <Group>
        <Button leftSection={<IconSend size={18} />} disabled={!canSubmit} loading={isLoading} onClick={handleSubmit}>
          {resubmit ? 'Отправить повторно' : 'Отправить на рассмотрение'}
        </Button>
      </Group>
    </Paper>
  );
}

function Requirement({ done, children }: { done: boolean; children: string }) {
  return (
    <List.Item
      icon={
        <ThemeIcon size={20} radius="xl" color={done ? 'teal' : 'gray'} variant={done ? 'filled' : 'light'}>
          {done ? <IconCheck size={12} /> : <IconCircleDashed size={12} />}
        </ThemeIcon>
      }
    >
      <Text size="sm" c={done ? undefined : 'dimmed'}>
        {children}
      </Text>
    </List.Item>
  );
}

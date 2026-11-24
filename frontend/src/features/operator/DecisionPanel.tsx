import { Button, Group, Modal, Paper, Stack, Text, Textarea, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconArrowBackUp, IconCheck, IconX } from '@tabler/icons-react';
import { useState } from 'react';

import { type ApiError, fieldErrors } from '../../api/errors';
import { useDecideMutation } from '../../api/operatorApi';
import type { Application, DecisionAction } from '../../api/types';
import { notifyError, notifySuccess } from '../../lib/notify';
import { decisionCommentSchema } from '../../lib/validation';

const DECISIONS: Record<
  DecisionAction,
  { label: string; title: string; color: string; icon: typeof IconCheck; commentRequired: boolean; done: string }
> = {
  approve: {
    label: 'Одобрить',
    title: 'Одобрить заявку?',
    color: 'teal',
    icon: IconCheck,
    commentRequired: false,
    done: 'Заявка одобрена',
  },
  return: {
    label: 'Вернуть на доработку',
    title: 'Вернуть заявку на доработку',
    color: 'orange',
    icon: IconArrowBackUp,
    commentRequired: true,
    done: 'Заявка возвращена на доработку',
  },
  reject: {
    label: 'Отклонить',
    title: 'Отклонить заявку',
    color: 'red',
    icon: IconX,
    commentRequired: true,
    done: 'Заявка отклонена, оплата возвращена заявителю',
  },
};

export function DecisionPanel({ application }: { application: Application }) {
  const [action, setAction] = useState<DecisionAction | null>(null);
  const available = (Object.keys(DECISIONS) as DecisionAction[]).filter((key) =>
    application.allowed_actions.includes(key),
  );
  if (available.length === 0) return null;

  return (
    <Paper withBorder p="lg">
      <Title order={4} mb={4}>
        Решение
      </Title>
      <Text size="sm" c="dimmed" mb="md">
        При возврате на доработку и отклонении нужен комментарий — его увидит заявитель.
      </Text>
      <Group gap="sm">
        {available.map((key) => {
          const { label, color, icon: Icon } = DECISIONS[key];
          return (
            <Button
              key={key}
              color={color}
              variant={key === 'approve' ? 'filled' : 'light'}
              leftSection={<Icon size={18} />}
              onClick={() => setAction(key)}
            >
              {label}
            </Button>
          );
        })}
      </Group>

      {action && <DecisionModal application={application} action={action} onClose={() => setAction(null)} />}
    </Paper>
  );
}

function DecisionModal({
  application,
  action,
  onClose,
}: {
  application: Application;
  action: DecisionAction;
  onClose: () => void;
}) {
  const [decide, { isLoading }] = useDecideMutation();
  const decision = DECISIONS[action];
  const form = useForm({
    initialValues: { comment: '' },
    validate: {
      comment: (value) => {
        if (!decision.commentRequired && !value.trim()) return null;
        const result = decisionCommentSchema.safeParse(value);
        return result.success ? null : result.error.issues[0]?.message;
      },
    },
  });

  const handleSubmit = form.onSubmit(async ({ comment }) => {
    try {
      await decide({ id: application.id, action, comment: comment.trim() || null }).unwrap();
      notifySuccess(decision.done);
      onClose();
    } catch (error) {
      const apiError = error as ApiError;
      const errors = fieldErrors(apiError);
      if (Object.keys(errors).length > 0) {
        form.setErrors(errors);
        return;
      }
      // например, другой оператор уже принял решение — карточка обновится
      notifyError(error);
      onClose();
    }
  });

  return (
    <Modal opened onClose={onClose} title={<Text fw={700}>{decision.title}</Text>} centered>
      <form onSubmit={handleSubmit} noValidate>
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            {application.full_name} · {application.service_type.name}
          </Text>
          {action === 'reject' && (
            <Text size="sm">Оплата будет автоматически возвращена заявителю.</Text>
          )}
          <Textarea
            label={decision.commentRequired ? 'Причина' : 'Комментарий'}
            placeholder={
              decision.commentRequired ? 'Что нужно исправить или почему заявка отклонена' : 'Необязательно'
            }
            withAsterisk={decision.commentRequired}
            autosize
            minRows={3}
            maxLength={1000}
            data-autofocus
            {...form.getInputProps('comment')}
          />
          <Group justify="flex-end" gap="sm">
            <Button variant="default" onClick={onClose}>
              Отмена
            </Button>
            <Button type="submit" color={decision.color} loading={isLoading}>
              {decision.label}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

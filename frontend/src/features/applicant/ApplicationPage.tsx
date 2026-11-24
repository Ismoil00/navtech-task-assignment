import { Alert, Anchor, Button, Grid, Group, Paper, Skeleton, Stack, Text, Title } from '@mantine/core';
import { modals } from '@mantine/modals';
import { IconArrowLeft, IconMessageExclamation, IconPencil, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router';

import {
  useDeleteApplicationMutation,
  useGetMyApplicationQuery,
  useUpdateApplicationMutation,
} from '../../api/applicationsApi';
import type { Application } from '../../api/types';
import { ApplicationDetails } from '../../components/ApplicationDetails';
import { PageHeader } from '../../components/PageHeader';
import { ErrorState } from '../../components/States';
import { StatusBadge } from '../../components/StatusBadge';
import { StatusTimeline } from '../../components/StatusTimeline';
import { formatDateTime } from '../../lib/format';
import { notifyError, notifySuccess } from '../../lib/notify';
import { routes } from '../../lib/routes';
import { ApplicationForm } from './ApplicationForm';
import { ApplicationProgress } from './ApplicationProgress';
import { DocumentSection } from './DocumentSection';
import { PaymentSection } from './PaymentSection';
import { SubmitSection } from './SubmitSection';

export function ApplicationPage() {
  const { id = '' } = useParams();
  const { data: application, error, isLoading, refetch } = useGetMyApplicationQuery(id);

  if (isLoading) {
    return (
      <Stack>
        <Skeleton h={40} w={320} />
        <Skeleton h={90} />
        <Skeleton h={260} />
      </Stack>
    );
  }
  if (error || !application) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <>
      <Anchor component={Link} to={routes.myApplications} size="sm" mb="sm" display="inline-flex">
        <Group gap={4}>
          <IconArrowLeft size={16} /> Мои заявки
        </Group>
      </Anchor>
      <PageHeader
        title={application.service_type.name}
        description={`Заявка от ${formatDateTime(application.created_at)}`}
        actions={
          <Group gap="sm">
            {application.allowed_actions.includes('delete') && <DeleteDraftButton id={application.id} />}
            <StatusBadge status={application.status} size="lg" />
          </Group>
        }
      />

      <OperatorDecisionBanner application={application} />
      <ApplicationProgress application={application} />
      {application.payment?.status === 'processing' && <PaymentStatusPoller id={application.id} />}

      <Grid gutter="lg">
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="lg">
            <DetailsSection application={application} />
            <DocumentSection application={application} />
            <PaymentSection application={application} />
            <SubmitSection application={application} />
          </Stack>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <StatusTimeline history={application.history} />
        </Grid.Col>
      </Grid>
    </>
  );
}

function DeleteDraftButton({ id }: { id: string }) {
  const navigate = useNavigate();
  const [deleteApplication, { isLoading }] = useDeleteApplicationMutation();

  const confirm = () =>
    modals.openConfirmModal({
      title: 'Удалить черновик?',
      children: <Text size="sm">Черновик пропадёт из списка заявок. Это действие нельзя отменить.</Text>,
      labels: { confirm: 'Удалить', cancel: 'Отмена' },
      confirmProps: { color: 'red' },
      onConfirm: async () => {
        try {
          await deleteApplication(id).unwrap();
          notifySuccess('Черновик удалён');
          navigate(routes.myApplications, { replace: true });
        } catch (error) {
          notifyError(error);
        }
      },
    });

  return (
    <Button variant="subtle" color="red" size="xs" leftSection={<IconTrash size={14} />} loading={isLoading} onClick={confirm}>
      Удалить черновик
    </Button>
  );
}

/** Пока платёж в обработке, перечитываем заявку раз в 2 секунды до окончательного статуса. */
function PaymentStatusPoller({ id }: { id: string }) {
  useGetMyApplicationQuery(id, { pollingInterval: 2000, skipPollingIfUnfocused: false });
  return null;
}

function DetailsSection({ application }: { application: Application }) {
  const [editing, setEditing] = useState(false);
  const [updateApplication] = useUpdateApplicationMutation();
  const canEdit = application.allowed_actions.includes('edit');

  return (
    <Paper withBorder p="lg">
      <Group justify="space-between" mb="md">
        <Title order={4}>Данные заявки</Title>
        {canEdit && !editing && (
          <Button variant="light" size="xs" leftSection={<IconPencil size={14} />} onClick={() => setEditing(true)}>
            Изменить
          </Button>
        )}
      </Group>
      {editing && canEdit ? (
        <ApplicationForm
          submitLabel="Сохранить"
          serviceTypeLocked={application.status !== 'draft'}
          initialValues={{
            full_name: application.full_name,
            phone: application.phone,
            service_type_id: String(application.service_type.id),
            comment: application.comment ?? '',
          }}
          onCancel={() => setEditing(false)}
          onSubmit={async (input) => {
            try {
              await updateApplication({ id: application.id, changes: input }).unwrap();
              notifySuccess('Изменения сохранены');
              setEditing(false);
            } catch (error) {
              notifyError(error);
              throw error;
            }
          }}
        />
      ) : (
        <ApplicationDetails application={application} />
      )}
    </Paper>
  );
}

/** Комментарий оператора при возврате на доработку или отклонении. */
function OperatorDecisionBanner({ application }: { application: Application }) {
  if (application.status !== 'returned' && application.status !== 'rejected') return null;
  const decision = [...application.history]
    .reverse()
    .find((entry) => entry.actor.role === 'operator' && entry.to_status === application.status);
  const returned = application.status === 'returned';

  return (
    <Alert
      mb="lg"
      color={returned ? 'orange' : 'red'}
      variant="light"
      icon={<IconMessageExclamation size={20} />}
      title={returned ? 'Заявка возвращена на доработку' : 'Заявка отклонена'}
    >
      <Text size="sm">{decision?.comment}</Text>
      <Text size="xs" c="dimmed" mt={4}>
        {returned
          ? 'Исправьте данные или документ и отправьте заявку снова — платить повторно не нужно.'
          : 'Оплата возвращена. Чтобы подать заявку заново, создайте новую.'}
      </Text>
    </Alert>
  );
}

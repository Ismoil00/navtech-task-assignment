import { Anchor, Badge, Grid, Group, Paper, Skeleton, Stack, Text, Title } from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';
import { Link, useParams } from 'react-router';

import { useGetOperatorApplicationQuery } from '../../api/operatorApi';
import type { Application } from '../../api/types';
import { ApplicationDetails } from '../../components/ApplicationDetails';
import { DocumentCard } from '../../components/DocumentCard';
import { PageHeader } from '../../components/PageHeader';
import { ErrorState } from '../../components/States';
import { StatusBadge } from '../../components/StatusBadge';
import { StatusTimeline } from '../../components/StatusTimeline';
import { formatDateTime, formatMoney } from '../../lib/format';
import { routes } from '../../lib/routes';
import { PAYMENT_COLORS, PAYMENT_LABELS } from '../../lib/statuses';
import { DecisionPanel } from './DecisionPanel';

export function ReviewPage() {
  const { id = '' } = useParams();
  const { data: application, error, isLoading, refetch } = useGetOperatorApplicationQuery(id);

  if (isLoading) {
    return (
      <Stack>
        <Skeleton h={40} w={320} />
        <Skeleton h={260} />
      </Stack>
    );
  }
  if (error || !application) return <ErrorState error={error} onRetry={refetch} />;

  return (
    <>
      <Anchor component={Link} to={routes.queue} size="sm" mb="sm" display="inline-flex">
        <Group gap={4}>
          <IconArrowLeft size={16} /> Очередь заявок
        </Group>
      </Anchor>
      <PageHeader
        title={application.service_type.name}
        description={`${application.full_name} · отправлена ${formatDateTime(application.submitted_at)}`}
        actions={<StatusBadge status={application.status} size="lg" />}
      />

      <Grid gutter="lg">
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="lg">
            <DecisionPanel application={application} />
            <Paper withBorder p="lg">
              <Title order={4} mb="md">
                Данные заявки
              </Title>
              <ApplicationDetails application={application} />
            </Paper>
            <Paper withBorder p="lg">
              <Title order={4} mb="md">
                Документ
              </Title>
              {application.attachment ? (
                <DocumentCard
                  attachment={application.attachment}
                  fileUrl={`/operator/applications/${application.id}/file`}
                />
              ) : (
                <Text size="sm" c="dimmed">
                  Документ не приложен
                </Text>
              )}
            </Paper>
            <PaymentInfo application={application} />
          </Stack>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <StatusTimeline history={application.history} />
        </Grid.Col>
      </Grid>
    </>
  );
}

function PaymentInfo({ application }: { application: Application }) {
  const { payment } = application;
  return (
    <Paper withBorder p="lg">
      <Group justify="space-between">
        <Title order={4}>Оплата</Title>
        {payment && (
          <Badge color={PAYMENT_COLORS[payment.status]} variant="light">
            {PAYMENT_LABELS[payment.status]}
          </Badge>
        )}
      </Group>
      {payment ? (
        <Text size="sm" mt="sm">
          {formatMoney(payment.amount, payment.currency)} ·{' '}
          {payment.status === 'refunded'
            ? `возвращена ${formatDateTime(payment.refunded_at)}`
            : formatDateTime(payment.updated_at)}
        </Text>
      ) : (
        <Text size="sm" c="dimmed" mt="sm">
          Нет оплаты
        </Text>
      )}
    </Paper>
  );
}

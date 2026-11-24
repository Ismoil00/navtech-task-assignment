import { Alert, Button, Group, Loader, Paper, Stack, Text, Title, Tooltip } from '@mantine/core';
import { IconAlertCircle, IconCircleCheck, IconCreditCard, IconReceiptRefund } from '@tabler/icons-react';

import type { Application } from '../../api/types';
import { formatDateTime, formatMoney } from '../../lib/format';
import { usePayment } from './usePayment';

export function PaymentSection({ application }: { application: Application }) {
  const { phase, error, pay } = usePayment(application.id);
  const { payment, service_type: service } = application;
  const amount = formatMoney(service.price, service.currency);
  const canPay = application.allowed_actions.includes('pay');
  // платёж в обработке на сервере (например, страницу перезагрузили во время оплаты)
  const serverProcessing = payment?.status === 'processing';
  const busy = phase === 'processing' || phase === 'slow' || serverProcessing;

  return (
    <Paper withBorder p="lg">
      <Group justify="space-between" mb="md">
        <Title order={4}>Оплата</Title>
        <Text fw={700} size="lg">
          {amount}
        </Text>
      </Group>

      <Stack gap="md">
        {payment?.status === 'succeeded' && (
          <Alert color="teal" variant="light" icon={<IconCircleCheck size={20} />} title="Оплачено">
            <Text size="sm">
              {formatMoney(payment.amount, payment.currency)} · {formatDateTime(payment.updated_at)}
            </Text>
            {application.status === 'returned' && (
              <Text size="xs" c="dimmed" mt={4}>
                Заявка возвращена на доработку — платить повторно не нужно.
              </Text>
            )}
          </Alert>
        )}

        {payment?.status === 'refunded' && (
          <Alert color="gray" variant="light" icon={<IconReceiptRefund size={20} />} title="Оплата возвращена">
            <Text size="sm">
              {formatMoney(payment.amount, payment.currency)} вернулись на карту ·{' '}
              {formatDateTime(payment.refunded_at)}
            </Text>
          </Alert>
        )}

        {(phase === 'slow' || serverProcessing) && (
          <Alert color="yellow" variant="light" icon={<Loader size={18} color="yellow" />} title="Платёж обрабатывается">
            <Text size="sm">
              Банк отвечает дольше обычного. Не закрывайте страницу — статус проверяется автоматически, повторного
              списания не будет.
            </Text>
          </Alert>
        )}

        {phase === 'failed' && error && (
          <Alert color="red" variant="light" icon={<IconAlertCircle size={20} />} title="Оплата не прошла">
            <Text size="sm">{error}</Text>
          </Alert>
        )}

        {phase !== 'failed' && payment?.status === 'failed' && !busy && (
          <Text size="sm" c="dimmed">
            Предыдущая попытка не прошла: {payment.failure_reason}
          </Text>
        )}

        {(canPay || busy) && payment?.status !== 'succeeded' && (
          <Group>
            <Button
              leftSection={<IconCreditCard size={18} />}
              loading={busy}
              onClick={pay}
              size="md"
            >
              {phase === 'failed' ? 'Попробовать ещё раз' : `Оплатить ${amount}`}
            </Button>
          </Group>
        )}

        {!canPay && !busy && application.status === 'draft' && !application.attachment && (
          <Tooltip label="Оплатить можно после того, как приложен документ">
            <Group>
              <Button leftSection={<IconCreditCard size={18} />} disabled size="md">
                Оплатить {amount}
              </Button>
            </Group>
          </Tooltip>
        )}
      </Stack>
    </Paper>
  );
}

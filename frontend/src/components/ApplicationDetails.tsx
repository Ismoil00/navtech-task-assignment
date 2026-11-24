import { SimpleGrid, Stack, Text } from '@mantine/core';
import type { ReactNode } from 'react';

import type { Application } from '../api/types';
import { formatDateTime, formatMoney, formatPhone } from '../lib/format';

/** Данные заявки только для чтения — общие для заявителя и оператора. */
export function ApplicationDetails({ application }: { application: Application }) {
  return (
    <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="lg" verticalSpacing="md">
      <Field label="ФИО">{application.full_name}</Field>
      <Field label="Телефон">{formatPhone(application.phone)}</Field>
      <Field label="Услуга">{application.service_type.name}</Field>
      <Field label="Стоимость">
        {formatMoney(application.service_type.price, application.service_type.currency)}
      </Field>
      <Field label="Создана">{formatDateTime(application.created_at)}</Field>
      <Field label="Отправлена">{formatDateTime(application.submitted_at)}</Field>
      <Field label="Комментарий" span>
        {application.comment || <Text span c="dimmed">Нет комментария</Text>}
      </Field>
    </SimpleGrid>
  );
}

function Field({ label, children, span }: { label: string; children: ReactNode; span?: boolean }) {
  return (
    <Stack gap={2} style={span ? { gridColumn: '1 / -1' } : undefined}>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600} lts={0.3}>
        {label}
      </Text>
      <Text size="sm" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
        {children}
      </Text>
    </Stack>
  );
}

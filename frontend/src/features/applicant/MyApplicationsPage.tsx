import {
  Button,
  Group,
  Pagination,
  Paper,
  Select,
  Skeleton,
  Stack,
  Table,
  Text,
} from '@mantine/core';
import { IconChevronRight, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router';

import { useListMyApplicationsQuery } from '../../api/applicationsApi';
import type { ApplicationStatus } from '../../api/types';
import { PageHeader } from '../../components/PageHeader';
import { EmptyState, ErrorState } from '../../components/States';
import { StatusBadge } from '../../components/StatusBadge';
import { formatDateTime, formatMoney } from '../../lib/format';
import { routes } from '../../lib/routes';
import { APPLICANT_NEXT_STEP, APPLICANT_STATUS_FILTER, STATUS_LABELS } from '../../lib/statuses';

const PAGE_SIZE = 10;

export function MyApplicationsPage() {
  const navigate = useNavigate();
  const [status, setStatus] = useState<ApplicationStatus | null>(null);
  const [page, setPage] = useState(1);
  const { data, isLoading, isFetching, error, refetch } = useListMyApplicationsQuery({
    status,
    page,
    pageSize: PAGE_SIZE,
  });

  const newButton = (
    <Button component={Link} to={routes.newApplication} leftSection={<IconPlus size={18} />}>
      Новая заявка
    </Button>
  );

  return (
    <>
      <PageHeader
        title="Мои заявки"
        description="Все ваши заявки и их текущий статус"
        actions={newButton}
      />

      <Group mb="md">
        <Select
          placeholder="Все статусы"
          clearable
          w={240}
          data={APPLICANT_STATUS_FILTER.map((value) => ({ value, label: STATUS_LABELS[value] }))}
          value={status}
          onChange={(value) => {
            setStatus(value as ApplicationStatus | null);
            setPage(1);
          }}
        />
      </Group>

      {error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : isLoading ? (
        <Stack gap="xs">
          {Array.from({ length: 4 }, (_, index) => (
            <Skeleton key={index} h={56} radius="md" />
          ))}
        </Stack>
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title={status ? 'Нет заявок с таким статусом' : 'У вас пока нет заявок'}
          description={
            status
              ? 'Попробуйте выбрать другой статус'
              : 'Создайте заявку: заполните данные, приложите документ, оплатите и отправьте на рассмотрение'
          }
          action={status ? undefined : newButton}
        />
      ) : (
        <Stack gap="md">
          <Paper withBorder style={{ overflow: 'hidden', opacity: isFetching ? 0.7 : 1 }}>
            <Table.ScrollContainer minWidth={720}>
              <Table highlightOnHover verticalSpacing="sm" horizontalSpacing="md">
                <Table.Thead bg="gray.0">
                  <Table.Tr>
                    <Table.Th>Услуга</Table.Th>
                    <Table.Th>Создана</Table.Th>
                    <Table.Th w={190}>Статус</Table.Th>
                    <Table.Th>Что дальше</Table.Th>
                    <Table.Th w={40} />
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {data.items.map((item) => (
                    <Table.Tr
                      key={item.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(routes.myApplication(item.id))}
                    >
                      <Table.Td>
                        <Text fw={500} size="sm">
                          {item.service_type.name}
                        </Text>
                        <Text c="dimmed" size="xs">
                          {formatMoney(item.service_type.price, item.service_type.currency)}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{formatDateTime(item.created_at)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <StatusBadge status={item.status} />
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm" c="dimmed">
                          {APPLICANT_NEXT_STEP[item.status]}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <IconChevronRight size={18} color="var(--mantine-color-gray-5)" />
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          </Paper>

          <Group justify="space-between">
            <Text size="sm" c="dimmed">
              Всего: {data.total}
            </Text>
            {data.pages > 1 && <Pagination total={data.pages} value={page} onChange={setPage} />}
          </Group>
        </Stack>
      )}
    </>
  );
}

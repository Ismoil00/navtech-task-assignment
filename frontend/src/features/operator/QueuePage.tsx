import { Group, Pagination, Paper, Select, Skeleton, Stack, Table, Text } from '@mantine/core';
import { IconChevronRight } from '@tabler/icons-react';
import { useNavigate, useSearchParams } from 'react-router';

import { useListQueueQuery } from '../../api/operatorApi';
import { useGetServiceTypesQuery } from '../../api/serviceTypesApi';
import type { ApplicationStatus } from '../../api/types';
import { PageHeader } from '../../components/PageHeader';
import { EmptyState, ErrorState } from '../../components/States';
import { StatusBadge } from '../../components/StatusBadge';
import { formatDateTime, formatMoney } from '../../lib/format';
import { routes } from '../../lib/routes';
import { OPERATOR_STATUS_FILTER, STATUS_LABELS } from '../../lib/statuses';

const PAGE_SIZE = 10;
const ALL = 'all';

export function QueuePage() {
  const navigate = useNavigate();
  // фильтры живут в адресной строке: после обновления страницы или «назад» они сохраняются
  const [params, setParams] = useSearchParams();
  const statusParam = params.get('status') ?? 'submitted'; // по умолчанию — заявки, ждущие решения
  const status = statusParam === ALL ? null : (statusParam as ApplicationStatus);
  const serviceTypeId = params.get('service') ? Number(params.get('service')) : null;
  const page = Number(params.get('page') ?? '1') || 1;

  const { data: serviceTypes = [] } = useGetServiceTypesQuery();
  const { data, isLoading, isFetching, error, refetch } = useListQueueQuery({
    status,
    serviceTypeId,
    page,
    pageSize: PAGE_SIZE,
  });

  const updateParams = (changes: Record<string, string | null>) => {
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(changes)) {
      if (value === null) next.delete(key);
      else next.set(key, value);
    }
    setParams(next);
  };

  return (
    <>
      <PageHeader title="Очередь заявок" description="Отправленные на рассмотрение заявки" />

      <Group mb="md" gap="sm">
        <Select
          label="Статус"
          w={240}
          allowDeselect={false}
          data={[
            { value: ALL, label: 'Все отправленные' },
            ...OPERATOR_STATUS_FILTER.map((value) => ({ value, label: STATUS_LABELS[value] })),
          ]}
          value={statusParam}
          onChange={(value) => updateParams({ status: value, page: null })}
        />
        <Select
          label="Услуга"
          placeholder="Все услуги"
          clearable
          w={320}
          data={serviceTypes.map((service) => ({ value: String(service.id), label: service.name }))}
          value={serviceTypeId ? String(serviceTypeId) : null}
          onChange={(value) => updateParams({ service: value, page: null })}
        />
      </Group>

      {error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : isLoading ? (
        <Stack gap="xs">
          {Array.from({ length: 5 }, (_, index) => (
            <Skeleton key={index} h={52} radius="md" />
          ))}
        </Stack>
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="Заявок нет"
          description="По выбранным фильтрам ничего не найдено. Попробуйте изменить статус или услугу."
        />
      ) : (
        <Stack gap="md">
          <Paper withBorder style={{ overflow: 'hidden', opacity: isFetching ? 0.7 : 1 }}>
            <Table.ScrollContainer minWidth={760}>
              <Table highlightOnHover verticalSpacing="sm" horizontalSpacing="md">
                <Table.Thead bg="gray.0">
                  <Table.Tr>
                    <Table.Th>Заявитель</Table.Th>
                    <Table.Th>Услуга</Table.Th>
                    <Table.Th>Отправлена</Table.Th>
                    <Table.Th w={190}>Статус</Table.Th>
                    <Table.Th w={40} />
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {data.items.map((item) => (
                    <Table.Tr
                      key={item.id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => navigate(routes.review(item.id))}
                    >
                      <Table.Td>
                        <Text size="sm" fw={500}>
                          {item.full_name}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{item.service_type.name}</Text>
                        <Text size="xs" c="dimmed">
                          {formatMoney(item.service_type.price, item.service_type.currency)}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        <Text size="sm">{formatDateTime(item.submitted_at)}</Text>
                      </Table.Td>
                      <Table.Td>
                        <StatusBadge status={item.status} />
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
              Найдено: {data.total}
            </Text>
            {data.pages > 1 && (
              <Pagination
                total={data.pages}
                value={page}
                onChange={(value) => updateParams({ page: String(value) })}
              />
            )}
          </Group>
        </Stack>
      )}
    </>
  );
}

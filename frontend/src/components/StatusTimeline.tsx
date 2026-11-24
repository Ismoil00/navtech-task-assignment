import { Paper, Text, ThemeIcon, Timeline, Title } from '@mantine/core';
import { IconCircleDot } from '@tabler/icons-react';

import type { HistoryEntry } from '../api/types';
import { formatDateTime } from '../lib/format';
import { STATUS_COLORS, STATUS_LABELS } from '../lib/statuses';

const ROLE_LABELS = { applicant: 'заявитель', operator: 'оператор' } as const;

/** История заявки: кто, когда и с каким комментарием менял статус. */
export function StatusTimeline({ history }: { history: HistoryEntry[] }) {
  return (
    <Paper withBorder p="lg">
      <Title order={4} mb="lg">
        История
      </Title>
      <Timeline active={history.length - 1} bulletSize={26} lineWidth={2}>
        {history.map((entry) => (
          <Timeline.Item
            key={entry.id}
            bullet={
              <ThemeIcon size={26} radius="xl" color={STATUS_COLORS[entry.to_status]} variant="light">
                <IconCircleDot size={14} />
              </ThemeIcon>
            }
            title={
              <Text size="sm" fw={600}>
                {entry.from_status === null ? 'Создан черновик' : STATUS_LABELS[entry.to_status]}
              </Text>
            }
          >
            <Text size="xs" c="dimmed">
              {entry.actor.full_name} · {ROLE_LABELS[entry.actor.role]}
            </Text>
            <Text size="xs" c="dimmed">
              {formatDateTime(entry.created_at)}
            </Text>
            {entry.comment && (
              <Text size="sm" mt={6} p="xs" bg="gray.0" style={{ borderRadius: 8, whiteSpace: 'pre-wrap' }}>
                {entry.comment}
              </Text>
            )}
          </Timeline.Item>
        ))}
      </Timeline>
    </Paper>
  );
}

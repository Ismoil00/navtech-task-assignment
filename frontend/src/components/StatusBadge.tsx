import { Badge, type BadgeProps } from '@mantine/core';

import type { ApplicationStatus } from '../api/types';
import { STATUS_COLORS, STATUS_LABELS } from '../lib/statuses';

export function StatusBadge({ status, ...props }: { status: ApplicationStatus } & BadgeProps) {
  return (
    <Badge color={STATUS_COLORS[status]} variant="light" radius="sm" {...props}>
      {STATUS_LABELS[status]}
    </Badge>
  );
}

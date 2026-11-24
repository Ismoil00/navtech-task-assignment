import { Paper, Stepper } from '@mantine/core';
import { IconCreditCard, IconFileUpload, IconPencil, IconSend } from '@tabler/icons-react';

import type { Application } from '../../api/types';

const SENT_STATUSES = new Set(['submitted', 'approved', 'rejected']);
const PAID_STATUSES = new Set(['paid', 'submitted', 'approved', 'rejected', 'returned']);

/** Путь заявки: данные -> документ -> оплата -> отправка. Показывает, что уже сделано. */
export function ApplicationProgress({ application }: { application: Application }) {
  const done = [
    true,
    application.attachment !== null,
    PAID_STATUSES.has(application.status),
    SENT_STATUSES.has(application.status),
  ];
  const firstOpen = done.indexOf(false);
  const active = firstOpen === -1 ? done.length : firstOpen;

  return (
    <Paper withBorder p="lg" mb="lg">
      <Stepper active={active} size="sm" allowNextStepsSelect={false}>
        <Stepper.Step icon={<IconPencil size={18} />} label="Данные" description="Заполнены" />
        <Stepper.Step
          icon={<IconFileUpload size={18} />}
          label="Документ"
          description={done[1] ? 'Приложен' : 'PDF, JPG или PNG'}
        />
        <Stepper.Step
          icon={<IconCreditCard size={18} />}
          label="Оплата"
          description={done[2] ? 'Оплачено' : 'Нужно оплатить'}
        />
        <Stepper.Step
          icon={<IconSend size={18} />}
          label="Отправка"
          description={
            application.status === 'returned' ? 'Отправьте снова' : done[3] ? 'Отправлена' : 'На рассмотрение'
          }
        />
      </Stepper>
    </Paper>
  );
}

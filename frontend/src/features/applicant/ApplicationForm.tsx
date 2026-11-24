import { Button, Group, Select, Stack, Textarea, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';

import { type ApiError, fieldErrors } from '../../api/errors';
import { useGetServiceTypesQuery } from '../../api/serviceTypesApi';
import type { ApplicationInput } from '../../api/types';
import { formatMoney } from '../../lib/format';
import { applicationSchema, zodValidator } from '../../lib/validation';

export interface ApplicationFormValues {
  full_name: string;
  phone: string;
  service_type_id: string | null;
  comment: string;
}

interface ApplicationFormProps {
  initialValues: ApplicationFormValues;
  submitLabel: string;
  /** После оплаты услугу менять нельзя: от неё зависела списанная сумма. */
  serviceTypeLocked?: boolean;
  onSubmit: (input: ApplicationInput) => Promise<void>;
  onCancel?: () => void;
}

export function ApplicationForm({
  initialValues,
  submitLabel,
  serviceTypeLocked = false,
  onSubmit,
  onCancel,
}: ApplicationFormProps) {
  // справочник уже в store: его загрузили сразу после входа
  const { data: serviceTypes = [], isLoading } = useGetServiceTypesQuery();
  const form = useForm<ApplicationFormValues>({
    initialValues,
    validate: zodValidator<ApplicationFormValues>(applicationSchema),
    validateInputOnBlur: true,
  });

  const handleSubmit = form.onSubmit(async (values) => {
    try {
      await onSubmit({
        full_name: values.full_name.trim(),
        phone: values.phone.trim(),
        service_type_id: Number(values.service_type_id),
        comment: values.comment.trim() || null,
      });
    } catch (error) {
      // ошибки полей от сервера показываем под соответствующими полями
      form.setErrors(fieldErrors(error as ApiError));
    }
  });

  return (
    <form onSubmit={handleSubmit} noValidate>
      <Stack gap="md">
        <TextInput
          label="ФИО"
          placeholder="Фамилия Имя Отчество"
          withAsterisk
          autoComplete="name"
          {...form.getInputProps('full_name')}
        />
        <TextInput
          label="Телефон"
          placeholder="+992 93 123 4567"
          description="Номер без кода страны считается таджикским"
          withAsterisk
          autoComplete="tel"
          inputMode="tel"
          {...form.getInputProps('phone')}
        />
        <Select
          label="Услуга"
          placeholder={isLoading ? 'Загрузка…' : 'Выберите услугу'}
          withAsterisk
          searchable
          nothingFoundMessage="Ничего не найдено"
          disabled={serviceTypeLocked}
          description={serviceTypeLocked ? 'После оплаты услугу изменить нельзя' : undefined}
          data={serviceTypes.map((service) => ({
            value: String(service.id),
            label: `${service.name} — ${formatMoney(service.price, service.currency)}`,
          }))}
          {...form.getInputProps('service_type_id')}
        />
        <Textarea
          label="Комментарий"
          placeholder="Необязательно: уточнения для оператора"
          autosize
          minRows={3}
          maxRows={8}
          maxLength={1000}
          description={`${form.values.comment.length} / 1000`}
          {...form.getInputProps('comment')}
        />
        <Group justify="flex-end" gap="sm">
          {onCancel && (
            <Button variant="default" onClick={onCancel}>
              Отмена
            </Button>
          )}
          <Button type="submit" loading={form.submitting}>
            {submitLabel}
          </Button>
        </Group>
      </Stack>
    </form>
  );
}

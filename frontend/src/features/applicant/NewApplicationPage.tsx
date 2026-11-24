import { Grid, Paper, Stack, Text, ThemeIcon, Title } from '@mantine/core';
import { IconCreditCard, IconFileUpload, IconPencil, IconSend } from '@tabler/icons-react';
import { useNavigate } from 'react-router';

import { useCreateApplicationMutation } from '../../api/applicationsApi';
import { useAppSelector } from '../../app/hooks';
import { PageHeader } from '../../components/PageHeader';
import { notifyError, notifySuccess } from '../../lib/notify';
import { routes } from '../../lib/routes';
import { selectUser } from '../auth/authSlice';
import { ApplicationForm } from './ApplicationForm';

const STEPS = [
  { icon: IconPencil, title: 'Заполните данные', text: 'ФИО, телефон и услуга' },
  { icon: IconFileUpload, title: 'Приложите документ', text: 'PDF, JPG или PNG до 5 МБ' },
  { icon: IconCreditCard, title: 'Оплатите', text: 'Сумма зависит от услуги' },
  { icon: IconSend, title: 'Отправьте', text: 'Оператор рассмотрит заявку' },
];

export function NewApplicationPage() {
  const navigate = useNavigate();
  const user = useAppSelector(selectUser);
  const [createApplication] = useCreateApplicationMutation();

  return (
    <>
      <PageHeader
        title="Новая заявка"
        description="Заявка сохранится как черновик — её можно будет изменить до оплаты"
      />
      <Grid gutter="lg">
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Paper withBorder p="lg">
            <ApplicationForm
              submitLabel="Сохранить черновик"
              initialValues={{
                full_name: user?.full_name ?? '',
                phone: '',
                service_type_id: null,
                comment: '',
              }}
              onCancel={() => navigate(routes.myApplications)}
              onSubmit={async (input) => {
                try {
                  const application = await createApplication(input).unwrap();
                  notifySuccess('Черновик сохранён. Теперь приложите документ');
                  navigate(routes.myApplication(application.id), { replace: true });
                } catch (error) {
                  notifyError(error);
                  throw error;
                }
              }}
            />
          </Paper>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper withBorder p="lg" bg="indigo.0">
            <Title order={5} mb="md">
              Как подать заявку
            </Title>
            <Stack gap="md">
              {STEPS.map(({ icon: Icon, title, text }, index) => (
                <Stack key={title} gap={2}>
                  <Text size="sm" fw={600}>
                    <ThemeIcon size={22} radius="xl" variant="light" mr={8} style={{ verticalAlign: 'middle' }}>
                      <Icon size={13} />
                    </ThemeIcon>
                    {index + 1}. {title}
                  </Text>
                  <Text size="xs" c="dimmed" pl={30}>
                    {text}
                  </Text>
                </Stack>
              ))}
            </Stack>
          </Paper>
        </Grid.Col>
      </Grid>
    </>
  );
}

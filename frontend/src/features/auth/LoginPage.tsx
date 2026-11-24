import {
  Alert,
  Anchor,
  Box,
  Button,
  Group,
  List,
  Paper,
  PasswordInput,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  ThemeIcon,
  Title,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import {
  IconAlertCircle,
  IconCreditCard,
  IconFileCheck,
  IconShieldCheck,
  IconUserCheck,
} from '@tabler/icons-react';
import { useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router';

import { useLoginMutation } from '../../api/authApi';
import type { UserRole } from '../../api/types';
import { useAppSelector } from '../../app/hooks';
import { asApiError } from '../../lib/notify';
import { homePath } from '../../lib/routes';
import { selectUser } from './authSlice';

// Демо-пользователи из backend/scripts/seed.py — подсказка для проверяющих
const DEMO_ACCOUNTS: Record<UserRole, string[]> = {
  applicant: ['applicant1', 'applicant2', 'applicant3'],
  operator: ['operator1', 'operator2'],
};

const PORTAL_OPTIONS = [
  { value: 'applicant', label: 'Заявитель' },
  { value: 'operator', label: 'Оператор' },
];

export function LoginPage() {
  const user = useAppSelector(selectUser);
  const navigate = useNavigate();
  const location = useLocation();
  const [login, { isLoading }] = useLoginMutation();
  const [portal, setPortal] = useState<UserRole>('applicant');
  const [error, setError] = useState<string | null>(null);

  const form = useForm({
    initialValues: { username: '', password: '' },
    validate: {
      username: (value) => (value.trim() ? null : 'Введите логин'),
      password: (value) => (value ? null : 'Введите пароль'),
    },
  });

  if (user) return <Navigate to={homePath(user.role)} replace />;

  const handleSubmit = form.onSubmit(async (values) => {
    setError(null);
    try {
      const result = await login({ ...values, username: values.username.trim(), portal }).unwrap();
      const from = (location.state as { from?: string } | null)?.from;
      const home = homePath(result.user.role);
      navigate(from?.startsWith(home) ? from : home, { replace: true });
    } catch (caught) {
      setError(asApiError(caught)?.message ?? 'Не удалось войти. Попробуйте ещё раз');
    }
  });

  const fillDemo = (username: string) => {
    form.setValues({ username, password: `${username}pass` });
    setError(null);
  };

  return (
    <SimpleGrid cols={{ base: 1, md: 2 }} spacing={0} mih="100vh">
      <Box
        visibleFrom="md"
        p={56}
        style={{
          background: 'linear-gradient(135deg, var(--mantine-color-indigo-7), var(--mantine-color-violet-6))',
          color: 'white',
        }}
      >
        <Stack justify="center" h="100%" maw={460} gap="xl">
          <Title order={1} fw={700}>
            Сервис подачи заявок
          </Title>
          <Text size="lg" opacity={0.9}>
            Подайте заявку на услугу онлайн и следите за её рассмотрением.
          </Text>
          <List spacing="md" size="md" center>
            <List.Item icon={<FeatureIcon icon={<IconFileCheck size={18} />} />}>
              Заполните заявку и приложите документ
            </List.Item>
            <List.Item icon={<FeatureIcon icon={<IconCreditCard size={18} />} />}>
              Оплатите услугу — повторный клик не спишет деньги дважды
            </List.Item>
            <List.Item icon={<FeatureIcon icon={<IconUserCheck size={18} />} />}>
              Оператор рассмотрит заявку и примет решение
            </List.Item>
          </List>
        </Stack>
      </Box>

      <Stack justify="center" align="center" p="xl" bg="gray.0">
        <Paper withBorder shadow="sm" p="xl" w="100%" maw={420}>
          <Stack gap="lg">
            <div>
              <Title order={2}>Вход</Title>
              <Text c="dimmed" size="sm">
                Выберите кабинет и войдите под своей учётной записью
              </Text>
            </div>

            <SegmentedControl
              fullWidth
              data={PORTAL_OPTIONS}
              value={portal}
              onChange={(value) => {
                setPortal(value as UserRole);
                setError(null);
              }}
            />

            <form onSubmit={handleSubmit} noValidate>
              <Stack gap="md">
                <TextInput
                  label="Логин"
                  autoComplete="username"
                  autoFocus
                  {...form.getInputProps('username')}
                />
                <PasswordInput
                  label="Пароль"
                  autoComplete="current-password"
                  {...form.getInputProps('password')}
                />
                {error && (
                  <Alert color="red" icon={<IconAlertCircle size={18} />} variant="light">
                    {error}
                  </Alert>
                )}
                <Button type="submit" fullWidth loading={isLoading} size="md">
                  Войти
                </Button>
              </Stack>
            </form>

            <Paper bg="indigo.0" p="sm" radius="md">
              <Group gap={6} mb={4}>
                <IconShieldCheck size={16} color="var(--mantine-color-indigo-7)" />
                <Text size="sm" fw={600} c="indigo.8">
                  Демо-доступ
                </Text>
              </Group>
              <Text size="xs" c="dimmed" mb={6}>
                Пароль — логин с окончанием «pass». Нажмите, чтобы подставить:
              </Text>
              <Group gap="xs">
                {DEMO_ACCOUNTS[portal].map((username) => (
                  <Anchor key={username} component="button" type="button" size="sm" onClick={() => fillDemo(username)}>
                    {username}
                  </Anchor>
                ))}
              </Group>
            </Paper>
          </Stack>
        </Paper>
      </Stack>
    </SimpleGrid>
  );
}

function FeatureIcon({ icon }: { icon: React.ReactNode }) {
  return (
    <ThemeIcon size={32} radius="xl" color="white" variant="white" c="indigo.7">
      {icon}
    </ThemeIcon>
  );
}

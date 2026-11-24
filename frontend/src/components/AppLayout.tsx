import {
  AppShell,
  Avatar,
  Badge,
  Button,
  Container,
  Group,
  Menu,
  Text,
  ThemeIcon,
  UnstyledButton,
} from '@mantine/core';
import { IconChevronDown, IconFileText, IconLogout } from '@tabler/icons-react';
import { NavLink, Outlet, useNavigate } from 'react-router';

import { useLogoutMutation } from '../api/authApi';
import { useAppSelector } from '../app/hooks';
import { selectUser } from '../features/auth/authSlice';
import { homePath, routes } from '../lib/routes';

const ROLE_LABELS = { applicant: 'Заявитель', operator: 'Оператор' } as const;

export function AppLayout() {
  const user = useAppSelector(selectUser);
  const navigate = useNavigate();
  const [logout] = useLogoutMutation();

  if (!user) return null;

  const links =
    user.role === 'applicant'
      ? [
          { to: routes.myApplications, label: 'Мои заявки', end: true },
          { to: routes.newApplication, label: 'Новая заявка', end: true },
        ]
      : [{ to: routes.queue, label: 'Очередь заявок', end: false }];

  const handleLogout = async () => {
    await logout();
    navigate(routes.login, { replace: true });
  };

  return (
    <AppShell header={{ height: 64 }} padding="lg" bg="gray.0">
      <AppShell.Header>
        <Container size="lg" h="100%">
          <Group h="100%" justify="space-between" wrap="nowrap">
            <Group gap="xl" wrap="nowrap">
              <UnstyledButton onClick={() => navigate(homePath(user.role))}>
                <Group gap="xs" wrap="nowrap">
                  <ThemeIcon size={34} radius="md" variant="gradient" gradient={{ from: 'indigo', to: 'violet' }}>
                    <IconFileText size={20} />
                  </ThemeIcon>
                  <Text fw={700} visibleFrom="sm">
                    Подача заявок
                  </Text>
                </Group>
              </UnstyledButton>
              <Group gap={4} wrap="nowrap">
                {links.map((link) => (
                  <NavLink key={link.to} to={link.to} end={link.end}>
                    {({ isActive }) => (
                      <Button variant={isActive ? 'light' : 'subtle'} color={isActive ? 'indigo' : 'gray'} size="sm">
                        {link.label}
                      </Button>
                    )}
                  </NavLink>
                ))}
              </Group>
            </Group>

            <Menu position="bottom-end" width={220} shadow="md">
              <Menu.Target>
                <UnstyledButton>
                  <Group gap="xs" wrap="nowrap">
                    <Avatar color="indigo" radius="xl" size={34}>
                      {initials(user.full_name)}
                    </Avatar>
                    <div style={{ lineHeight: 1.2 }}>
                      <Text size="sm" fw={600} visibleFrom="sm">
                        {user.full_name}
                      </Text>
                      <Badge size="xs" variant="light" color={user.role === 'operator' ? 'grape' : 'indigo'}>
                        {ROLE_LABELS[user.role]}
                      </Badge>
                    </div>
                    <IconChevronDown size={16} />
                  </Group>
                </UnstyledButton>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Label>{user.username}</Menu.Label>
                <Menu.Item color="red" leftSection={<IconLogout size={16} />} onClick={handleLogout}>
                  Выйти
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Group>
        </Container>
      </AppShell.Header>

      <AppShell.Main>
        <Container size="lg" py="md">
          <Outlet />
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}

function initials(fullName: string): string {
  return fullName
    .split(' ')
    .slice(0, 2)
    .map((part) => part[0] ?? '')
    .join('')
    .toUpperCase();
}

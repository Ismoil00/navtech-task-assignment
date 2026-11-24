import { expect, type Page } from '@playwright/test';

type Portal = 'Заявитель' | 'Оператор';

/** Вход через форму, как это делает пользователь. Пароль демо-учёток — логин + «pass». */
export async function login(page: Page, portal: Portal, username: string): Promise<void> {
  await page.goto('/login');
  await page.getByText(portal, { exact: true }).click();
  await page.getByLabel('Логин').fill(username);
  await page.getByLabel('Пароль').fill(`${username}pass`);
  await page.getByRole('button', { name: 'Войти' }).click();
  await expect(page).not.toHaveURL(/\/login/);
}

export async function logout(page: Page): Promise<void> {
  await page.getByRole('banner').getByRole('button').last().click();
  await page.getByRole('menuitem', { name: 'Выйти' }).click();
  await expect(page).toHaveURL(/\/login/);
}

/**
 * Уникальное ФИО, чтобы найти именно эту заявку в очереди оператора,
 * даже если в базе уже есть другие заявки. Только буквы — как требует валидация.
 */
export function uniqueFullName(): string {
  const letters = 'абвгдежзиклмнопрстуфхцчшэюя';
  const suffix = Array.from({ length: 6 }, () => letters[Math.floor(Math.random() * letters.length)]).join('');
  return `Тестов${suffix} Сквозной Сценарий`;
}

export const PDF_FILE = {
  name: 'Диплом.pdf',
  mimeType: 'application/pdf',
  buffer: Buffer.from('%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF'),
};

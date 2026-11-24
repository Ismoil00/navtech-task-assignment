/**
 * Основной сценарий через интерфейс:
 * заявитель создаёт заявку, прикладывает документ, оплачивает и отправляет;
 * оператор находит её в очереди по фильтрам, открывает, скачивает файл и
 * возвращает на доработку с комментарием; заявитель исправляет и отправляет
 * снова без повторной оплаты; оператор одобряет.
 */
import { expect, test } from '@playwright/test';

import { login, logout, PDF_FILE, uniqueFullName } from './helpers';

test('заявка проходит путь от черновика до одобрения с возвратом на доработку', async ({ page }) => {
  const fullName = uniqueFullName();
  const returnComment = 'Скан нечитаемый, загрузите файл в лучшем качестве';

  // --- Заявитель: создаёт черновик ---
  await login(page, 'Заявитель', 'applicant1');
  await page.getByRole('link', { name: 'Новая заявка' }).first().click();
  await page.getByLabel('ФИО').fill(fullName);
  await page.getByLabel('Телефон').fill('93 555 1234');
  await page.getByRole('textbox', { name: 'Услуга' }).click();
  await page.getByRole('option', { name: /Апостиль на документ/ }).click();
  await page.getByRole('button', { name: 'Сохранить черновик' }).click();

  await expect(page).toHaveURL(/\/applications\/[0-9a-f-]{36}$/);
  const applicationUrl = page.url();
  const applicationId = applicationUrl.split('/').pop()!;
  await expect(page.getByText('Черновик', { exact: true }).first()).toBeVisible();

  // --- Прикладывает документ ---
  await page.locator('input[type="file"]').setInputFiles(PDF_FILE);
  await expect(page.getByText(PDF_FILE.name)).toBeVisible();

  // --- Оплачивает ---
  await page.getByRole('button', { name: /Оплатить/ }).click();
  await expect(page.getByText('Оплачено', { exact: true }).first()).toBeVisible();

  // --- Отправляет на рассмотрение ---
  await page.getByRole('button', { name: 'Отправить на рассмотрение' }).click();
  await expect(page.getByText('На рассмотрении', { exact: true }).first()).toBeVisible();
  await logout(page);

  // --- Оператор: находит заявку в очереди по фильтрам ---
  await login(page, 'Оператор', 'operator1');
  await expect(page).toHaveURL(/\/operator\/applications/);
  await page.getByRole('textbox', { name: 'Услуга' }).click();
  await page.getByRole('option', { name: 'Апостиль на документ' }).click();
  await expect(page).toHaveURL(/service=/);
  await page.getByRole('row', { name: new RegExp(fullName) }).click();
  await expect(page).toHaveURL(new RegExp(`/operator/applications/${applicationId}$`));

  // --- Скачивает приложенный файл ---
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Скачать' }).click();
  expect((await downloadPromise).suggestedFilename()).toBe(PDF_FILE.name);

  // --- Возвращает на доработку: без комментария нельзя ---
  await page.getByRole('button', { name: 'Вернуть на доработку' }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByRole('button', { name: 'Вернуть на доработку' }).click();
  await expect(dialog.getByText('Укажите причину — не меньше 5 символов')).toBeVisible();
  await dialog.getByLabel('Причина').fill(returnComment);
  await dialog.getByRole('button', { name: 'Вернуть на доработку' }).click();
  await expect(page.getByText('На доработке', { exact: true }).first()).toBeVisible();
  await logout(page);

  // --- Заявитель видит причину, исправляет и отправляет снова без оплаты ---
  await login(page, 'Заявитель', 'applicant1');
  await page.goto(applicationUrl);
  await expect(page.getByText('Заявка возвращена на доработку', { exact: true })).toBeVisible();
  await expect(page.getByText(returnComment).first()).toBeVisible();
  await expect(page.getByText('платить повторно не нужно').first()).toBeVisible();

  await page.getByRole('button', { name: 'Изменить' }).click();
  await page.getByLabel('Комментарий').fill('Загрузил скан в лучшем качестве');
  await page.getByRole('button', { name: 'Сохранить', exact: true }).click();
  await page.locator('input[type="file"]').setInputFiles({ ...PDF_FILE, name: 'Диплом-новый.pdf' });
  await expect(page.getByText('Диплом-новый.pdf')).toBeVisible();

  // кнопки оплаты нет: заявка уже оплачена
  await expect(page.getByRole('button', { name: /Оплатить/ })).toHaveCount(0);
  await page.getByRole('button', { name: 'Отправить повторно' }).click();
  await expect(page.getByText('На рассмотрении', { exact: true }).first()).toBeVisible();
  await logout(page);

  // --- Оператор одобряет ---
  await login(page, 'Оператор', 'operator1');
  await page.goto(`/operator/applications/${applicationId}`);
  await page.getByRole('button', { name: 'Одобрить' }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Одобрить' }).click();
  await expect(page.getByText('Одобрена', { exact: true }).first()).toBeVisible();

  // --- История: каждый шаг с автором ---
  const history = page.getByText('История').locator('..');
  for (const step of ['Создан черновик', 'Оплачена', 'На рассмотрении', 'На доработке', 'Одобрена']) {
    await expect(history.getByText(step, { exact: true }).first()).toBeVisible();
  }
});

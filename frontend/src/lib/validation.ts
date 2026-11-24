// Правила проверки полей — те же, что на сервере (backend/app/schemas/application.py).
// Фронтенд проверяет заранее для удобства, сервер всё равно проверяет заново.
import { isValidPhoneNumber } from 'libphonenumber-js';
import { z } from 'zod';

export const DEFAULT_PHONE_COUNTRY = 'TJ';
export const MAX_DOCUMENT_SIZE = 5 * 1024 * 1024;
export const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png'];
export const ALLOWED_MIME_TYPES = ['application/pdf', 'image/jpeg', 'image/png'];

// буквы любого алфавита (в том числе таджикские ғ ӣ қ ӯ ҳ ҷ), пробел, дефис, апостроф, точка
const NAME_PATTERN = /^[\p{L}\s\-'’ʼ.]+$/u;

const collapseSpaces = (value: string) => value.trim().replace(/\s+/g, ' ');

export const fullNameSchema = z
  .string()
  .transform(collapseSpaces)
  .pipe(
    z
      .string()
      .min(3, 'ФИО должно содержать от 3 до 150 символов')
      .max(150, 'ФИО должно содержать от 3 до 150 символов')
      .regex(NAME_PATTERN, 'ФИО может содержать только буквы, пробел, дефис, апостроф и точку')
      .refine(
        (value) => value.split(' ').filter((word) => /\p{L}/u.test(word)).length >= 2,
        'Укажите как минимум фамилию и имя',
      ),
  );

export const phoneSchema = z
  .string()
  .trim()
  .min(1, 'Укажите номер телефона')
  .refine((value) => isValidPhoneNumber(value, DEFAULT_PHONE_COUNTRY), 'Некорректный номер телефона');

export const applicationSchema = z.object({
  full_name: fullNameSchema,
  phone: phoneSchema,
  service_type_id: z.preprocess((value) => value ?? '', z.string().min(1, 'Выберите услугу')),
  comment: z.string().max(1000, 'Не больше 1000 символов'),
});

export const decisionCommentSchema = z
  .string()
  .trim()
  .min(5, 'Укажите причину — не меньше 5 символов')
  .max(1000, 'Не больше 1000 символов');

/** Проверка файла до отправки: тип по расширению и размер. Содержимое проверит сервер. */
export function validateDocument(file: File): string | null {
  const name = file.name.toLowerCase();
  if (!ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension))) {
    return 'Допустимы только файлы PDF, JPG или PNG';
  }
  if (file.size === 0) return 'Файл пустой';
  if (file.size > MAX_DOCUMENT_SIZE) return 'Файл больше 5 МБ';
  return null;
}

/** Адаптер: схема zod -> функция validate для @mantine/form. */
export function zodValidator<T>(schema: z.ZodType) {
  return (values: T): Record<string, string> => {
    const result = schema.safeParse(values);
    if (result.success) return {};
    const errors: Record<string, string> = {};
    for (const issue of result.error.issues) {
      const field = String(issue.path[0] ?? '');
      if (field && !(field in errors)) errors[field] = issue.message;
    }
    return errors;
  };
}

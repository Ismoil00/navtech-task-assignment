import { useCallback, useRef, useState } from 'react';

import { applicationsApi, cacheApplication } from '../../api/applicationsApi';
import { toApiError } from '../../api/errors';
import { http } from '../../api/http';
import type { Application } from '../../api/types';
import { useAppDispatch } from '../../app/hooks';
import { notifySuccess } from '../../lib/notify';
import { newUuid } from '../../lib/uuid';

/** idle — ждём нажатия; processing — запрос отправлен; slow — шлюз отвечает долго, проверяем статус. */
export type PaymentPhase = 'idle' | 'processing' | 'slow' | 'failed';

const CLIENT_TIMEOUT_MS = 7_000; // дольше ответа не ждём — переходим к проверке статуса
const POLL_INTERVAL_MS = 2_000;
const MAX_WAIT_MS = 90_000;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Оплата без двойного списания.
 *
 * На каждую попытку создаётся один Idempotency-Key. Если ответ не пришёл вовремя
 * (таймаут, обрыв сети) или сервер ответил «ещё обрабатывается» (202), запрос
 * повторяется с ТЕМ ЖЕ ключом — сервер вернёт результат той же попытки, а не
 * спишет деньги снова. Новый ключ появляется только после окончательного отказа.
 */
export function usePayment(applicationId: string) {
  const dispatch = useAppDispatch();
  const [phase, setPhase] = useState<PaymentPhase>('idle');
  const [error, setError] = useState<string | null>(null);
  const keyRef = useRef<string | null>(null);
  const runningRef = useRef(false);

  const pay = useCallback(async () => {
    if (runningRef.current) return; // повторный клик во время оплаты игнорируем
    runningRef.current = true;
    keyRef.current ??= newUuid();
    setError(null);
    setPhase('processing');
    const startedAt = Date.now();

    try {
      for (;;) {
        try {
          const response = await http.post<Application>(`/applications/${applicationId}/payments`, null, {
            headers: { 'Idempotency-Key': keyRef.current },
            timeout: CLIENT_TIMEOUT_MS,
          });
          cacheApplication(dispatch, response.data);
          if (response.status === 200) {
            keyRef.current = null;
            setPhase('idle');
            notifySuccess('Оплата прошла. Теперь заявку можно отправить на рассмотрение');
            return;
          }
          setPhase('slow'); // 202: шлюз ещё обрабатывает
        } catch (caught) {
          const apiError = toApiError(caught);
          const stillUnknown =
            apiError.status === 'TIMEOUT' ||
            apiError.status === 'NETWORK' ||
            apiError.code === 'PAYMENT_IN_PROGRESS';
          if (!stillUnknown) {
            // окончательный отказ (например, банк отклонил): следующая попытка — с новым ключом
            keyRef.current = null;
            setError(apiError.message);
            setPhase('failed');
            dispatch(applicationsApi.util.invalidateTags([{ type: 'Application', id: applicationId }]));
            return;
          }
          setPhase('slow'); // ответ не дошёл — результат узнаем повтором с тем же ключом
        }

        if (Date.now() - startedAt > MAX_WAIT_MS) {
          setError('Платёж всё ещё обрабатывается. Обновите страницу немного позже');
          setPhase('failed');
          return;
        }
        await sleep(POLL_INTERVAL_MS);
      }
    } finally {
      runningRef.current = false;
    }
  }, [applicationId, dispatch]);

  return { phase, error, pay };
}

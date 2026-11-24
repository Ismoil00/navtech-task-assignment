import { Alert, Group, Paper, Progress, Stack, Text, ThemeIcon, Title } from '@mantine/core';
import { Dropzone, type FileRejection } from '@mantine/dropzone';
import { IconAlertCircle, IconCloudUpload, IconFileCheck, IconX } from '@tabler/icons-react';
import { useState } from 'react';

import { cacheApplication } from '../../api/applicationsApi';
import { uploadDocument } from '../../api/documents';
import { isApiError } from '../../api/errors';
import type { Application } from '../../api/types';
import { useAppDispatch } from '../../app/hooks';
import { DocumentCard } from '../../components/DocumentCard';
import { notifySuccess } from '../../lib/notify';
import { ALLOWED_MIME_TYPES, MAX_DOCUMENT_SIZE, validateDocument } from '../../lib/validation';

export function DocumentSection({ application }: { application: Application }) {
  const dispatch = useAppDispatch();
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const canUpload = application.allowed_actions.includes('upload_file');
  const attachment = application.attachment;

  const upload = async (file: File) => {
    // быстрая проверка в браузере; содержимое файла всё равно проверит сервер
    const problem = validateDocument(file);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setProgress(0);
    try {
      const updated = await uploadDocument(application.id, file, setProgress);
      cacheApplication(dispatch, updated);
      notifySuccess(attachment ? 'Документ заменён' : 'Документ приложен');
    } catch (caught) {
      setError(isApiError(caught) ? caught.message : 'Не удалось загрузить файл');
    } finally {
      setProgress(null);
    }
  };

  const reject = (rejections: FileRejection[]) => {
    const file = rejections[0]?.file;
    setError(file ? validateDocument(file) ?? 'Этот файл загрузить нельзя' : 'Можно приложить только один файл');
  };

  return (
    <Paper withBorder p="lg">
      <Title order={4} mb={4}>
        Документ
      </Title>
      <Text size="sm" c="dimmed" mb="md">
        Один файл PDF, JPG или PNG размером до 5 МБ
      </Text>

      <Stack gap="md">
        {attachment ? (
          <DocumentCard attachment={attachment} fileUrl={`/applications/${application.id}/file`} />
        ) : (
          !canUpload && <Text size="sm" c="dimmed">Документ не приложен</Text>
        )}

        {canUpload && (
          <Dropzone
            onDrop={(files) => files[0] && upload(files[0])}
            onReject={reject}
            maxSize={MAX_DOCUMENT_SIZE}
            accept={ALLOWED_MIME_TYPES}
            multiple={false}
            loading={progress !== null}
            radius="md"
          >
            <Group justify="center" gap="md" mih={attachment ? 70 : 120} style={{ pointerEvents: 'none' }}>
              <Dropzone.Accept>
                <ThemeIcon size={48} radius="xl" variant="light" color="teal">
                  <IconFileCheck size={26} />
                </ThemeIcon>
              </Dropzone.Accept>
              <Dropzone.Reject>
                <ThemeIcon size={48} radius="xl" variant="light" color="red">
                  <IconX size={26} />
                </ThemeIcon>
              </Dropzone.Reject>
              <Dropzone.Idle>
                <ThemeIcon size={48} radius="xl" variant="light">
                  <IconCloudUpload size={26} />
                </ThemeIcon>
              </Dropzone.Idle>
              <div>
                <Text size="sm" fw={600}>
                  {attachment ? 'Заменить документ' : 'Перетащите файл сюда или нажмите, чтобы выбрать'}
                </Text>
                <Text size="xs" c="dimmed">
                  PDF, JPG или PNG, не больше 5 МБ
                </Text>
              </div>
            </Group>
          </Dropzone>
        )}

        {progress !== null && <Progress value={progress} animated size="sm" />}
        {error && (
          <Alert color="red" variant="light" icon={<IconAlertCircle size={18} />} withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </Stack>
    </Paper>
  );
}

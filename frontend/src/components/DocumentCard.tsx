import { Button, Group, Paper, Stack, Text, ThemeIcon } from '@mantine/core';
import { IconDownload, IconExternalLink, IconFileTypePdf, IconPhoto } from '@tabler/icons-react';
import { useState } from 'react';

import { downloadDocument, openDocument } from '../api/documents';
import type { Attachment } from '../api/types';
import { formatDateTime, formatFileSize } from '../lib/format';
import { notifyError } from '../lib/notify';

interface DocumentCardProps {
  attachment: Attachment;
  /** Адрес файла в API: у заявителя и оператора он разный. */
  fileUrl: string;
}

export function DocumentCard({ attachment, fileUrl }: DocumentCardProps) {
  const [busy, setBusy] = useState<'open' | 'download' | null>(null);
  const isPdf = attachment.content_type === 'application/pdf';

  const run = async (kind: 'open' | 'download') => {
    setBusy(kind);
    try {
      await (kind === 'open' ? openDocument(fileUrl) : downloadDocument(fileUrl));
    } catch (error) {
      notifyError(error, 'Не удалось получить документ');
    } finally {
      setBusy(null);
    }
  };

  return (
    <Paper withBorder p="md" radius="md" bg="gray.0">
      <Group justify="space-between" wrap="nowrap" gap="md">
        <Group gap="sm" wrap="nowrap" style={{ minWidth: 0 }}>
          <ThemeIcon size={44} radius="md" variant="light" color={isPdf ? 'red' : 'blue'}>
            {isPdf ? <IconFileTypePdf size={24} /> : <IconPhoto size={24} />}
          </ThemeIcon>
          <Stack gap={0} style={{ minWidth: 0 }}>
            <Text size="sm" fw={600} truncate="end">
              {attachment.original_filename}
            </Text>
            <Text size="xs" c="dimmed">
              {formatFileSize(attachment.size_bytes)} · загружен {formatDateTime(attachment.created_at)}
            </Text>
          </Stack>
        </Group>
        <Group gap="xs" wrap="nowrap">
          <Button
            size="xs"
            variant="default"
            leftSection={<IconExternalLink size={14} />}
            loading={busy === 'open'}
            onClick={() => run('open')}
          >
            Открыть
          </Button>
          <Button
            size="xs"
            variant="light"
            leftSection={<IconDownload size={14} />}
            loading={busy === 'download'}
            onClick={() => run('download')}
          >
            Скачать
          </Button>
        </Group>
      </Group>
    </Paper>
  );
}

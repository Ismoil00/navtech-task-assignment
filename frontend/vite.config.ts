import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  // в dev-режиме собираем библиотеки сразу при старте: иначе Vite дособирает их
  // на лету при первом открытии страницы и может подгрузить вторую копию React
  optimizeDeps: {
    include: ['@mantine/core', '@mantine/dropzone', '@mantine/modals', '@tabler/icons-react'],
  },
  preview: { port: 4173 },
  build: {
    rollupOptions: {
      output: {
        // библиотеки — отдельными файлами: они меняются редко и кешируются браузером
        manualChunks: {
          react: ['react', 'react-dom', 'react-router'],
          mantine: [
            '@mantine/core',
            '@mantine/hooks',
            '@mantine/form',
            '@mantine/notifications',
            '@mantine/dropzone',
            '@mantine/modals',
          ],
          redux: ['@reduxjs/toolkit', 'react-redux'],
        },
      },
    },
  },
});

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
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

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  root: 'src',
  build: {
    outDir: '../dist',
    emptyOutDir: true,
  },
  esbuild: {
    target: 'es2022',
  },
  server: {
    proxy: {
      '/convert': 'http://localhost:3000',
    },
  },
});

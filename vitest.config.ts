import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    coverage: {
      provider: 'v8',
      include: ['packages/*/src/**'],
    },
  },
  resolve: {
    alias: {
      '@pdf-darker/core': path.resolve(import.meta.dirname, 'packages/core/src'),
      '@pdf-darker/shared': path.resolve(import.meta.dirname, 'packages/shared/src'),
      '@pdf-darker/ui/server.js': path.resolve(import.meta.dirname, 'packages/ui/src/server.ts'),
    },
  },
});

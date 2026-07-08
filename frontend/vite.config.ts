import { readFileSync } from 'fs';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const { version } = JSON.parse(readFileSync('./package.json', 'utf-8')) as { version: string };

// Vite 8's rollupOptions types only accept the function form of manualChunks
// (the object-literal record form used pre-8 no longer type-checks).
const MANUAL_CHUNKS: Record<string, string[]> = {
  'react-vendor': ['react', 'react-dom', 'react-router-dom'],
  'mui-vendor': ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
  'form-vendor': ['react-hook-form', 'zod', '@hookform/resolvers'],
  'data-vendor': ['axios', 'zustand'],
};

function manualChunks(id: string): string | undefined {
  for (const [chunk, packages] of Object.entries(MANUAL_CHUNKS)) {
    if (packages.some((pkg) => id.includes(`/node_modules/${pkg}/`))) {
      return chunk;
    }
  }
  return undefined;
}

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(version),
  },
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks,
      },
    },
  },
});

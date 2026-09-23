import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The shared transport contract (shared/contracts.ts, shared/fixtures.json) lives
// one level above this app. Alias it so components import the single source of
// truth instead of a copied second contract.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@shared': fileURLToPath(new URL('../shared', import.meta.url)),
    },
  },
  server: {
    fs: {
      allow: [fileURLToPath(new URL('..', import.meta.url))],
    },
    proxy: {
      // Future API integration point: start FastAPI on :8000 and run
      // VITE_DATA_PROVIDER=http npm run dev
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})

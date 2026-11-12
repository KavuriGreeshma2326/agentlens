import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Listen on all interfaces so the dev server is reachable inside Docker.
    host: '0.0.0.0',
    port: 5173,
  },
})

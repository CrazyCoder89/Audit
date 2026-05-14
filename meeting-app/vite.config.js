import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],

  define: {
    global: 'window',
  },

  resolve: {
    alias: {
      buffer: 'buffer',
      process: 'process/browser',
    },
  },
})
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 开发模式下，前端跑在 5173，API 通过代理转发到 Python 后端，避免 CORS
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:18742',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:18742',
        ws: true,
      },
    },
  },
})

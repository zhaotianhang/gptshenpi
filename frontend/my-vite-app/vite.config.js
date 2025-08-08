import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
   server: {
    proxy: {
      '/api':{
        target: 'http://localhost:3000', // 你的 Python 后端地址
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '') // 移除 '/api' 前缀
      }
    }
  }
})

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ command }) => {
  return {
    base: command === 'serve' ? '/' : '/ai-code-learning/',
    plugins: [vue()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    server: {
      port: 5173,
      proxy: {
         // 1. 先写最具体的：判题专用
        '/api/judge': {
          target: 'http://localhost:3002', // 与本仓库 FastAPI 判题入口一致
          changeOrigin: true
        },
        '/api/resources': {
          target: 'http://localhost:3001',
          changeOrigin: true
        },
        '/api/ai/chat': {
          target: 'http://localhost:3000',
          changeOrigin: true
        },
        '/api': {
          target: 'http://localhost:3002',
          changeOrigin: true,
          ws: true
        }
      }
    }
  }
})

// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  // GitHub Pages 基础路径
  base: '/ai-code-learning/',
  // 插件配置
  plugins: [vue()],
  // 路径别名配置
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})
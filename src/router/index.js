import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/learn/:language', // 按语言学习路由
    name: 'Learn',
    component: () => import('@/views/Learn.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
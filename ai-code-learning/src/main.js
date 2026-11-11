import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import router from './router'
import App from './App.vue'
import './styles/motion.css'
import './styles/teacher.css'
import { migrateLegacyAuthToSession } from '@/utils/authStorage'
import { getAuthToken } from '@/utils/authStorage'

// 保存原始 fetch
const originalFetch = window.fetch

// 重写 fetch
window.fetch = async (url, options = {}) => {
  // 只对 /api/ 开头的请求添加 token（可根据需要调整）
  const isApiRequest = typeof url === 'string' && url.startsWith('/api/')
  const token = isApiRequest ? getAuthToken() : null

  if (token && isApiRequest) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  }

  return originalFetch(url, options)
}

const app = createApp(App)
migrateLegacyAuthToSession()
dayjs.locale('zh-cn')
// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')

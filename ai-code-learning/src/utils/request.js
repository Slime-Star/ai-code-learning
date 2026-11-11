import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getAuthToken } from '@/utils/authStorage'   // 导入 token 获取函数

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/',
  timeout: 60000
})

// 请求拦截器：自动添加 token
service.interceptors.request.use(
  (config) => {
    const token = getAuthToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理错误和业务状态
service.interceptors.response.use(
  (response) => {
    const res = response.data
    // 后端返回格式：{ success: true/false, data?: any, message?: string, detail?: string }
    if (res.success === false) {
      // 业务错误
      const errorMsg = res.message || res.detail || '操作失败'
      ElMessage.error(errorMsg)
      return Promise.reject(new Error(errorMsg))
    }
    // 成功时直接返回整个 res（包含 data, message 等）
    return res
  },
  (error) => {
    // #region debug-point A:axios-error
    fetch("ws://150.158.24.107/event", { method: "POST", body: JSON.stringify({ sessionId: "competition-404-toast", runId: "pre", hypothesisId: "A", location: "src/utils/request.js:response-error", msg: "[DEBUG] axios response error", data: { message: String(error?.message || ""), status: Number(error?.response?.status || 0), url: String(error?.config?.url || ""), method: String(error?.config?.method || ""), baseURL: String(error?.config?.baseURL || ""), hasAuthHeader: !!error?.config?.headers?.Authorization, origin: typeof window !== "undefined" ? String(window.location?.origin || "") : "", respData: error?.response?.status === 422 ? (error?.response?.data || null) : null }, ts: Date.now() }) }).catch(() => {});
    // #endregion
    // HTTP 状态码错误（4xx, 5xx）
    console.error('响应错误：', error)
    const status = error.response?.status
    const reqUrl = String(error?.config?.url || '')
    const silent404 =
      status === 404 &&
      (
        reqUrl === '/api/competitions/my-registrations' ||
        reqUrl.endsWith('/api/competitions/my-registrations') ||
        /^\/api\/competitions\/\d+$/.test(reqUrl) ||
        /^\/api\/competitions\/\d+\/problems$/.test(reqUrl)
      )
    if (status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      // 可选：清除本地 token 并跳转登录页
      // import { removeAuthToken } from '@/utils/authStorage'
      // removeAuthToken()
      // window.location.href = '/login'
    } else if (status === 403) {
      ElMessage.error('权限不足')
    } else if (!silent404) {
      ElMessage.error(error.message || '服务器错误')
    }
    return Promise.reject(error)
  }
)

export default service

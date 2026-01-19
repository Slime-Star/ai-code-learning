import axios from 'axios'

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_APP_BASE_API || '/',
  timeout: 60000 // 超时时间
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 可添加token等请求头
    return config
  },
  (error) => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    const res = response.data
    // 假设后端返回code=200为成功
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    console.error('响应错误：', error)
    ElMessage.error(error.message || '服务器错误')
    return Promise.reject(error)
  }
)

export default service
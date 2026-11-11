import { defineStore } from 'pinia'
import { getCurrentUser, removeCurrentUser } from '@/utils/authStorage'

export const useAiStore = defineStore('ai', {
  state: () => ({
    // 原有 AI 相关状态
    currentLang: 'javascript',
    currentCode: '',
    chatHistory: [],
    
    // 新增：用户登录相关状态（和你的 localStorage 对齐）
    isLogin: false,
    userInfo: {
      id: '',
      name: '',
      avatar: '',
      collectedCourses: []
    }
  }),

  actions: {
    // 原有 AI 相关方法
    updateCurrentLang(lang) {
      this.currentLang = lang
    },
    updateCurrentCode(code) {
      this.currentCode = code
    },
    clearChatHistory() {
      this.chatHistory = []
    },
    
    // 新增：同步登录状态（按标签页会话读取）
    syncLoginState() {
      const currentUser = getCurrentUser()
      if (currentUser) {
        this.isLogin = true
        this.userInfo = currentUser
      } else {
        this.isLogin = false
        this.userInfo = { id: '', name: '', avatar: '', collectedCourses: [] }
      }
    },
    
    // 新增：登出方法
    logout() {
      this.isLogin = false
      this.userInfo = { id: '', name: '', avatar: '', collectedCourses: [] }
      removeCurrentUser()
      localStorage.removeItem('rememberUser')
    }
  }
})

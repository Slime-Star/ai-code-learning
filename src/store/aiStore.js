import { defineStore } from 'pinia'

export const useAiStore = defineStore('ai', {
  state: () => ({
    // 聊天记录
    chatHistory: [],
    // 当前编辑的代码
    currentCode: '',
    // 当前选择的编程语言
    currentLang: 'javascript',
    // AI是否正在响应
    aiLoading: false
  }),
  actions: {
    // 添加聊天消息
    addChatMessage(message) {
      this.chatHistory.push(message)
    },
    // 清空聊天记录
    clearChatHistory() {
      this.chatHistory = []
    },
    // 更新当前代码
    updateCurrentCode(code) {
      this.currentCode = code
    },
    // 更新当前语言
    updateCurrentLang(lang) {
      this.currentLang = lang
      this.currentCode = '' // 切换语言清空代码
    }
  }
})
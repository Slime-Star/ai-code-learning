// src/store/aiStore.js（完整正确版本）
import { defineStore } from 'pinia'
import {getCurrentUser} from '@/utils/authStorage'

export const useAiStore = defineStore('ai', {
  state: () => ({
    ownerId: String(getCurrentUser()?.id || 'guest'),
    // 聊天记录（Pinia 响应式数组）
    chatHistory: [],
    // 当前编辑的代码
    currentCode: '',
    // 当前选择的编程语言
    currentLang: 'javascript',
    // AI是否正在响应
    aiLoading: false
  }),
  actions: {
    ensureOwner(id) {
      const next=String(id || 'guest')
      if(next!==this.ownerId){this.chatHistory=[];this.currentCode='';this.ownerId=next}
    },
    // 添加聊天消息（核心方法）
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
    // 更新当前语言（切换语言时清空代码）
    updateCurrentLang(lang) {
      this.currentLang = lang
      this.currentCode = ''
    }
  }
})

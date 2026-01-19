<template>
  <div class="ai-chat">
    <!-- 聊天记录 -->
    <div class="chat-history">
      <div 
        v-for="(msg, index) in chatHistory" 
        :key="index" 
        class="chat-message"
        :class="{ 'user-message': msg.role === 'user', 'ai-message': msg.role === 'ai' }"
      >
        <div class="message-avatar">
          <el-icon v-if="msg.role === 'user'"><User /></el-icon>
          <el-icon v-else><Message /></el-icon>
        </div>
        <div class="message-content">
          <div v-if="msg.role === 'ai' && msg.content" v-html="formatCode(msg.content)"></div>
          <div v-else>{{ msg.content }}</div>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="chat-input">
      <el-input
        v-model="inputMsg"
        type="textarea"
        :rows="3"
        placeholder="输入你的问题，比如：帮我解释这段代码、修复这个bug、优化这段逻辑..."
        @keyup.enter="sendMessage"
      ></el-input>
      <el-button 
        type="primary" 
        icon="ChatRound" 
        @click="sendMessage"
        :loading="aiLoading"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAiStore } from '@/store/aiStore'
import { User, Message, ChatRound } from '@element-plus/icons-vue'
import axios from '@/utils/request'

const aiStore = useAiStore()
const inputMsg = ref('')

// 计算属性获取聊天记录
const chatHistory = computed(() => aiStore.chatHistory)
const aiLoading = computed(() => aiStore.aiLoading)

// 格式化代码（给代码块加样式）
const formatCode = (content) => {
  // 匹配Markdown代码块 ```js ... ```
  return content.replace(/```([\s\S]*?)```/g, (match, code) => {
    const lang = code.split('\n')[0].trim() || aiStore.currentLang
    const pureCode = code.replace(lang, '').trim()
    return `<pre class="code-block"><code class="language-${lang}">${pureCode}</code></pre>`
  })
}

// 发送消息给AI
const sendMessage = async () => {
  if (!inputMsg.value.trim() || aiLoading.value) return

  // 添加用户消息到历史
  const userMsg = {
    role: 'user',
    content: inputMsg.value.trim()
  }
  aiStore.addChatMessage(userMsg)
  const tempInput = inputMsg.value
  inputMsg.value = ''

  // 设置AI加载状态
  aiStore.aiLoading = true

  try {
    // 调用AI接口（替换为你的实际接口）
    const res = await axios.post('/api/ai/chat', {
      message: tempInput,
      code: aiStore.currentCode,
      language: aiStore.currentLang
    })

    // 添加AI回复到历史
    aiStore.addChatMessage({
      role: 'ai',
      content: res.data.content
    })
  } catch (error) {
    aiStore.addChatMessage({
      role: 'ai',
      content: '抱歉，AI服务暂时不可用，请稍后再试。'
    })
    console.error('AI请求失败：', error)
  } finally {
    // 取消加载状态
    aiStore.aiLoading = false
    // 滚动到最新消息
    setTimeout(() => {
      const chatHistory = document.querySelector('.chat-history')
      chatHistory.scrollTop = chatHistory.scrollHeight
    }, 100)
  }
}
</script>

<style scoped>
.ai-chat {
  display: flex;
  flex-direction: column;
  height: 600px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.chat-history {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background-color: #f9fafb;
}

.chat-message {
  display: flex;
  margin-bottom: 16px;
  gap: 8px;
}

.user-message {
  justify-content: flex-end;
}

.user-message .message-content {
  background-color: #4096ff;
  color: white;
}

.ai-message .message-content {
  background-color: white;
  border: 1px solid #e5e7eb;
}

.message-avatar {
  display: flex;
  align-items: flex-start;
  padding-top: 4px;
}

.message-content {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 8px;
  line-height: 1.5;
}

.code-block {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

.chat-input {
  padding: 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 8px;
}

.chat-input el-input {
  flex: 1;
}
</style>
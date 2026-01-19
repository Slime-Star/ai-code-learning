<template>
  <div class="learn-container">
    <!-- 顶部导航 -->
    <div class="learn-header">
      <h1>AI 辅助编程学习平台</h1>
      <div class="progress-bar">
        <span>学习进度：{{ progress }}%</span>
        <div class="progress">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
      </div>
    </div>

    <!-- 主体内容区 -->
    <div class="learn-content">
      <!-- 左侧：编程练习区 -->
      <div class="editor-section">
        <h2>今日练习：{{ currentExercise.title }}</h2>
        <p class="exercise-desc">{{ currentExercise.description }}</p >
        <div class="code-editor">
          <textarea 
            v-model="userCode" 
            placeholder="请在这里编写你的代码..."
            rows="15"
          ></textarea>
        </div>
        <div class="editor-actions">
          <button @click="runCode">运行代码</button>
          <button @click="askAI">问 AI</button>
        </div>
        <div class="output-area" v-if="output">
          <h3>运行结果</h3>
          <pre>{{ output }}</pre>
        </div>
      </div>

      <!-- 右侧：AI 问答区 -->
      <div class="ai-section">
        <h2>AI 编程助手</h2>
        <div class="chat-history">
          <div 
            class="chat-message" 
            :class="{ 'ai-message': msg.from === 'ai', 'user-message': msg.from === 'user' }"
            v-for="(msg, index) in chatHistory" 
            :key="index"
          >
            {{ msg.content }}
          </div>
        </div>
        <div class="input-area">
          <input 
            v-model="aiInput" 
            placeholder="请输入你的问题，比如：这段代码为什么报错？..."
            @keyup.enter="sendMessage"
          >
          <button @click="sendMessage">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 学习进度
const progress = ref(25)

// 当前练习题目
const currentExercise = ref({
  title: "实现一个斐波那契数列函数",
  description: "编写一个 JavaScript 函数，输入一个正整数 n，返回第 n 个斐波那契数。"
})

// 用户代码
const userCode = ref('')
const output = ref('')

// AI 聊天
const aiInput = ref('')
const chatHistory = ref([
  { from: 'ai', content: '你好！我是你的AI编程助手，有什么问题随时问我～' }
])

// 运行代码
const runCode = () => {
  try {
    // 模拟代码运行
    const result = eval(userCode.value)
    output.value = `✅ 运行成功：\n${result}`
  } catch (error) {
    output.value = `❌ 运行错误：\n${error.message}`
  }
}

// 发送消息给AI
const sendMessage = () => {
  if (!aiInput.value.trim()) return
  chatHistory.value.push({ from: 'user', content: aiInput.value })
  // 模拟AI回复
  setTimeout(() => {
    chatHistory.value.push({ 
      from: 'ai', 
      content: `我理解你的问题了："${aiInput.value}"。这是一个很好的问题，我们可以这样解决...` 
    })
    aiInput.value = ''
  }, 800)
}

// 页面加载时初始化
onMounted(() => {
  console.log('Learn 页面加载完成')
})
</script>

<style scoped>
.learn-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.learn-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.progress-bar {
  margin-top: 1rem;
}

.progress {
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #42b983;
  transition: width 0.3s ease;
}

.learn-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 2rem;
}

.editor-section, .ai-section {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.code-editor textarea {
  width: 100%;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  resize: vertical;
  background: #fff;
}

.editor-actions {
  margin: 1rem 0;
  display: flex;
  gap: 1rem;
}

.editor-actions button {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.editor-actions button:first-child {
  background: #42b983;
  color: white;
}

.editor-actions button:last-child {
  background: #2563eb;
  color: white;
}

.output-area {
  margin-top: 1rem;
  padding: 1rem;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 4px;
}

.output-area pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

.chat-history {
  height: 300px;
  overflow-y: auto;
  margin-bottom: 1rem;
  padding: 1rem;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 4px;
}

.chat-message {
  margin-bottom: 0.8rem;
  padding: 0.6rem 1rem;
  border-radius: 4px;
  max-width: 80%;
}

.ai-message {
  background: #e6f7ff;
  color: #262626;
  margin-right: auto;
}

.user-message {
  background: #f0f9ff;
  color: #165dff;
  margin-left: auto;
}

.input-area {
  display: flex;
  gap: 0.5rem;
}

.input-area input {
  flex: 1;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.input-area button {
  padding: 0.6rem 1.2rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
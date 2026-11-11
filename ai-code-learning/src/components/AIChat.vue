<template>
  <div class="ai-chat-container">
    <!-- 聊天记录区域 -->
    <div class="chat-history" ref="chatHistoryRef">
      <div
  v-for="(msg, index) in aiStore.chatHistory"
  :key="index"
  :class="['chat-message', msg.role]"
>
  <!-- 用户消息：头像在右边，所以先渲染内容，再渲染头像 -->
  <template v-if="msg.role === 'user'">
    <div class="message-content user-plain" v-text="msg.content"></div>
    <div class="message-avatar">
      <img v-if="userAvatar" :src="userAvatar" class="avatar-img" alt="avatar" @error="onAvatarError" />
      <div v-else class="avatar-fallback">{{ userInitial }}</div>
    </div>
  </template>
  <!-- AI 消息 -->
  <template v-else>
    <div v-if="isLoading && !msg.content && index === aiStore.chatHistory.length - 1" class="message-content typing-indicator">
      <span class="typing-text">AI 正在思考</span>
      <span class="typing-dots"><span></span><span></span><span></span></span>
    </div>
    <div v-else-if="isTyping && index === typingIndex" class="message-content typing" v-text="msg.content"></div>
    <div v-else class="message-content"><div v-html="formatMessage(msg.content)"></div><small v-if="msg.provider" class="assistant-provider">来源：{{ msg.provider }}{{ msg.fallback?' · 备用服务':'' }}</small><el-button v-if="msg.error" link type="primary" size="small" :disabled="isLoading" @click="retryMessage(msg)">重试本次问题</el-button></div>
  </template>
</div>
    </div>

    <div v-if="isLoading" class="assistant-status"><span>正在等待助手回复…</span><button @click="cancelRequest">停止等待</button></div>
    <!-- 输入框区域 -->
    <div class="chat-input">
      <el-input
        v-model="inputMessage"
        maxlength="4000"
        placeholder="输入你的编程问题，比如：如何用Python写冒泡排序？"
        @keydown.enter="handleInputEnter"
        style="margin-right: 8px;"
        :disabled="isLoading"
      />
      <el-button type="primary" @click="sendMessage" :loading="isLoading" :disabled="isLoading || !inputMessage.trim()">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount, computed, onMounted } from 'vue'
import { useAiStore } from '@/store/aiStore'
import { ElMessage } from 'element-plus'
import {getCurrentUser} from '@/utils/authStorage'
import {assistantMarkdown as formatMessage} from '@/utils/assistantMarkdown'
import {requestAssistant,conversationHistory} from '@/utils/assistantClient'
import 'highlight.js/styles/github-dark.css'

const props=defineProps({errorContext:{type:String,default:''}})
const aiStore = useAiStore()
const inputMessage = ref('')
const chatHistoryRef = ref(null)
const isLoading = ref(false) // 加载状态
let typeTimer = null
let requestController = null,requestSequence=0,typingMessage=null,typingText='',owner=String(getCurrentUser()?.id || 'guest')
const userInfo = ref(getCurrentUser())
const avatarError = ref(false)
const typingIndex = ref(-1)
const isTyping = ref(false)

const syncUser = () => {
  const next=String(getCurrentUser()?.id || 'guest')
  aiStore.ensureOwner(next)
  if(next!==owner){cancelRequest();clearInterval(typeTimer);typeTimer=null;isTyping.value=false;aiStore.clearChatHistory();owner=next}
  userInfo.value = getCurrentUser()
  avatarError.value = false
}

onMounted(() => {
  syncUser()
  window.addEventListener('user-updated', syncUser)
  window.addEventListener('focus', syncUser)
  window.addEventListener('storage', syncUser)
})

onBeforeUnmount(() => {
  window.removeEventListener('user-updated', syncUser)
  window.removeEventListener('focus', syncUser)
  window.removeEventListener('storage', syncUser)
})

const userAvatar = computed(() => {
  if (avatarError.value) return ''
  return userInfo.value?.avatar || ''
})
const userInitial = computed(() => {
  const name = String(userInfo.value?.name || '').trim()
  return (name ? name.slice(0, 1) : 'U').toUpperCase()
})
const onAvatarError = () => {
  avatarError.value = true
}

function finishTyping(){
  if(typingMessage && aiStore.chatHistory.includes(typingMessage))typingMessage.content=typingText
  clearInterval(typeTimer);typeTimer=null;typingMessage=null;isTyping.value=false;typingIndex.value=-1
}
const startTypewriter = (target,fullText) => {
  finishTyping();typingMessage=target;typingText=fullText;target.fullContent=fullText;isTyping.value=true;typingIndex.value=aiStore.chatHistory.indexOf(target)
  const chars=Array.from(fullText),step=Math.max(2,Math.ceil(chars.length/45));let length=0
  typeTimer=setInterval(()=>{length+=step;if(aiStore.chatHistory.includes(target))target.content=chars.slice(0,length).join('');if(length>=chars.length)finishTyping()},20)
}

const handleInputEnter = (event) => {
  if (event.isComposing || event.keyCode === 229) return
  event.preventDefault()
  sendMessage()
}

let activeReply=null
function cancelRequest(){requestSequence++;requestController?.abort();requestController=null;isLoading.value=false;if(activeReply && !activeReply.content){activeReply.content='已停止等待，可以重试本次问题。';activeReply.error=true}}
async function deliver(target,payload){
  if(isLoading.value)return
  finishTyping();isLoading.value=true;target.content='';target.fullContent='';target.error=false;activeReply=target
  requestController=new AbortController();const current=++requestSequence
  try{
    const data=await requestAssistant(payload.message,payload.context,payload.history,{signal:requestController.signal})
    if(current!==requestSequence || !aiStore.chatHistory.includes(target))return
    target.provider=data.provider || 'AI';target.fallback=!!data.fallback
    startTypewriter(target,data.reply+(data.truncated?'\n\n回复较长，可继续追问需要展开的部分。':''))
  }catch(error){if(current===requestSequence && error.name!=='AbortError' && aiStore.chatHistory.includes(target)){target.content=error.message;target.error=true}}
  finally{if(current===requestSequence){isLoading.value=false;requestController=null}}
}
const sendMessage = async () => {
  if(isLoading.value)return
  const message=inputMessage.value.trim();if(!message)return
  finishTyping()
  const payload={message,context:{language:aiStore.currentLang || 'javascript',code:aiStore.currentCode || '',error:props.errorContext},history:conversationHistory(aiStore.chatHistory)}
  aiStore.addChatMessage({role:'user',content:message});aiStore.chatHistory.push({role:'assistant',content:'',retryPayload:payload});const target=aiStore.chatHistory.at(-1)
  inputMessage.value='';await deliver(target,payload)
}
function retryMessage(target){if(target.retryPayload)deliver(target,target.retryPayload)}

// 监听聊天记录变化，自动滚动到底部
watch(
  () => aiStore.chatHistory.length,
  async () => {
    await nextTick()
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight
    }
  }
)

onBeforeUnmount(() => {
  cancelRequest()
  finishTyping()
  if (typeTimer) {
    clearInterval(typeTimer)
    typeTimer = null
  }
  typingIndex.value = -1
  isTyping.value = false
})
</script>

<style scoped>
.ai-chat-container {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  font-family: 'Microsoft YaHei', sans-serif;
}

/* 聊天记录区域 */
.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 10px;
  scrollbar-width: thin;
  scrollbar-color: #4096ff #f5f7fa;
}

/* 自定义滚动条 */
.chat-history::-webkit-scrollbar {
  width: 6px;
}
.chat-history::-webkit-scrollbar-thumb {
  background-color: #4096ff;
  border-radius: 3px;
}
.chat-history::-webkit-scrollbar-track {
  background-color: #f5f7fa;
}

/* 消息容器 */
.chat-message {
  display: flex;
  margin-bottom: 12px;
  gap: 12px;
  align-items: flex-start;
}

.chat-message.user {
  justify-content: flex-end;
}

/* 头像样式 */
.message-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #e8f4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  overflow: hidden;
}

.chat-message.user .message-avatar {
  background: #4096ff;
  color: white;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: #fff;
}

/* 消息内容 */
.message-content {
  max-width: 78%;
  padding: 10px 12px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  line-height: 1.55;
  white-space: pre-wrap;
  font-size: 13px;
}

.chat-message.user .message-content {
  background: #4096ff;
  color: white;
  border-radius: 12px;
}

.message-content.typing {
  white-space: pre-wrap;
}

.message-content.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #374151;
}

.typing-text {
  font-weight: 700;
  color: #374151;
}

.typing-dots {
  display: inline-flex;
  gap: 4px;
  vertical-align: middle;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
  display: inline-block;
  animation: typing-bounce 1s infinite ease-in-out;
}

.typing-dots span:nth-child(2) { animation-delay: 0.15s; }
.typing-dots span:nth-child(3) { animation-delay: 0.3s; }

/* Markdown和代码块样式 */
.message-content :deep(h1),
.message-content :deep(h2),
.message-content :deep(h3) {
  margin: 8px 0;
  font-weight: 600;
}
.message-content :deep(h1) { font-size: 18px; }
.message-content :deep(h2) { font-size: 16px; }
.message-content :deep(h3) { font-size: 14px; }

.message-content :deep(p) { margin: 2px 0; }

.message-content :deep(br) { line-height: 1.2; }
.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}

/* 代码块样式 */
.message-content :deep(pre) {
  background: #1e1e1e !important;
  color: #ccc;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.5;
  margin: 8px 0;
}

.message-content :deep(code) {
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 13px;
  background: #f0f2f5;
  color: #e53935;
}

.chat-message.user .message-content :deep(code) {
  background: #53a8ff;
  color: white;
}

.message-content :deep(pre code) {
  background: transparent !important;
  color: #ccc !important;
  padding: 0;
}

@keyframes typing-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.6; }
  40% { transform: translateY(-4px); opacity: 1; }
}

/* 输入框区域 */
.chat-input {
  display: flex;
  align-items: center;
  padding: 8px 0;
}

.chat-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  padding: 6px 12px;
}
</style>

<style scoped>
.user-plain{white-space:pre-wrap}.assistant-provider{display:block;font-size:10px;color:#a18caf;margin-top:12px}.assistant-status{display:flex;justify-content:space-between;font-size:11px;color:#a18caf;padding:7px 0}.assistant-status button{background:none;border:0;font:inherit;color:#9270b1;cursor:pointer}
</style>

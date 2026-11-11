<template>
  <div class="wx-page">
    <div class="wx-container">
      <div class="wx-shell">
        <div class="wx-rail">
          <el-avatar class="rail-avatar" :size="40" :src="me?.avatar || ''">{{ (me?.name || me?.username || '?').slice(0, 1) }}</el-avatar>
          <div class="rail-nav">
            <button class="rail-btn" :class="{ active: sidebarTab === 'conversations' }" @click="sidebarTab = 'conversations'">
              <el-icon><ChatDotRound /></el-icon>
            </button>
            <button v-if="isStudent" class="rail-btn" :class="{ active: sidebarTab === 'friends' }" @click="sidebarTab = 'friends'">
              <el-icon><UserFilled /></el-icon>
            </button>
          </div>
          <div class="rail-bottom">
            <button class="rail-btn subtle" title="刷新" @click="refreshAll" :disabled="loadingConversations">
              <el-icon><Refresh /></el-icon>
            </button>
          </div>
        </div>

        <div class="wx-list">
          <div class="list-top">
            <div class="list-title">{{ sidebarTab === 'conversations' ? '会话' : '好友' }}</div>
            <el-input v-if="sidebarTab === 'conversations'" v-model="convKeyword" clearable placeholder="搜索会话" class="search">
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <div v-else class="friend-tools">
              <el-autocomplete
                v-model="friendSearchText"
                class="friend-search"
                clearable
                :debounce="520"
                :trigger-on-focus="false"
                placeholder="搜索昵称/账号/ID"
                :fetch-suggestions="queryFriendSuggestions"
                @select="handleFriendSelect"
                @clear="clearFriendSelection"
              >
                <template #default="{ item }">
                  <div class="suggest-item">
                    <el-avatar :size="28" :src="item.avatar || ''">{{ (item.name || item.username || '?').slice(0, 1) }}</el-avatar>
                    <div class="suggest-meta">
                      <div class="suggest-name">{{ item.name || item.username }}</div>
                      <div class="suggest-sub mono">{{ item.username }} · {{ item.id }}</div>
                    </div>
                  </div>
                </template>
              </el-autocomplete>
              <el-button
                type="primary"
                :loading="addingFriend"
                :disabled="!selectedFriendId"
                @click="sendFriendRequestSelected"
              >
                添加
              </el-button>
            </div>
          </div>

          <div v-if="sidebarTab === 'conversations'" class="list-body">
            <el-skeleton v-if="loadingConversations && filteredConversations.length === 0" :rows="8" animated />
            <el-empty v-else-if="!loadingConversations && filteredConversations.length === 0" description="暂无会话" />
            <div v-else class="conv-list">
              <button
                v-for="c in filteredConversations"
                :key="c.id"
                class="conv-item"
                :class="{ active: c.id === activeConversationId }"
                @click="openConversation(c)"
              >
                <div class="conv-avatar">
                  <el-badge :value="c.unread" :hidden="!c.unread" :max="99">
                    <el-avatar :size="40" :src="avatarOf(c)">{{ initialOf(c) }}</el-avatar>
                  </el-badge>
                </div>
                <div class="conv-main">
                  <div class="conv-title">
                    <span class="conv-name">{{ titleOf(c) }}</span>
                    <span class="conv-time">{{ formatTime(c.lastMessage?.at) }}</span>
                  </div>
                  <div class="conv-preview">{{ previewOf(c) }}</div>
                </div>
              </button>
            </div>
          </div>

          <div v-else class="list-body">
            <div class="section-h">好友申请</div>
            <el-skeleton v-if="loadingFriends && incomingRequests.length === 0" :rows="4" animated />
            <el-empty v-else-if="!loadingFriends && incomingRequests.length === 0" description="暂无申请" />
            <div v-else class="req-list">
              <div v-for="r in incomingRequests" :key="r.id" class="req-item">
                <div class="req-user">
                  <el-avatar :size="36" :src="r.fromAvatar || ''">{{ (r.fromName || '').slice(0, 1) }}</el-avatar>
                  <div class="req-meta">
                    <div class="req-name">{{ r.fromName || r.fromUserId }}</div>
                    <div class="req-id mono">ID：{{ r.fromUserId }}</div>
                  </div>
                </div>
                <div class="req-actions" v-if="r.status === 'pending'">
                  <el-button size="small" type="success" :loading="respondingId === r.id" @click="respondRequest(r.id, 'accept')">同意</el-button>
                  <el-button size="small" plain :loading="respondingId === r.id" @click="respondRequest(r.id, 'reject')">拒绝</el-button>
                </div>
                <div class="req-status" v-else>
                  {{ r.status === 'accepted' ? '已同意' : '已拒绝' }}
                </div>
              </div>
            </div>

            <div class="section-h mt">我的好友</div>
            <el-skeleton v-if="loadingFriends && friends.length === 0" :rows="6" animated />
            <el-empty v-else-if="!loadingFriends && friends.length === 0" description="暂无好友" />
            <div v-else class="friend-list">
              <button v-for="f in friends" :key="f.id" class="friend-item" @click="startDm(f.id)">
                <el-avatar :size="40" :src="f.avatar || ''">{{ (f.name || '').slice(0, 1) }}</el-avatar>
                <div class="friend-meta">
                  <div class="friend-name">{{ f.name || f.id }}</div>
                  <div class="friend-id mono">ID：{{ f.id }}</div>
                </div>
              </button>
            </div>
          </div>
        </div>

        <div class="wx-chat">
          <div v-if="!activeConversationId" class="chat-empty">
            <TopicArt scene="chat" compact />
            <el-empty description="选择一个会话开始聊天" />
          </div>
          <div v-else class="chat-panel">
            <div class="chat-header">
              <div class="chat-header-left">
                <div class="chat-name">{{ activeTitle }}</div>
                <div class="chat-sub" v-if="activeConversation?.type === 'class'">班级群</div>
              </div>
              <div class="chat-header-right">
                <el-button
                  v-if="activeConversation?.type === 'class'"
                  plain
                  size="small"
                  @click="openClassInfo"
                  :loading="classInfoLoading"
                >班级信息</el-button>
                <el-button plain size="small" @click="loadNewMessages(false)" :loading="loadingMessages">刷新</el-button>
              </div>
            </div>

            <div ref="msgListRef" class="chat-body">
              <el-skeleton v-if="loadingMessages && messages.length === 0" :rows="10" animated />
              <el-empty v-else-if="!loadingMessages && messages.length === 0" description="暂无消息" />
              <div v-else class="msg-list">
                <div
                  v-for="m in messages"
                  :key="m.id"
                  class="msg-row"
                  :class="{ mine: String(m.senderId) === String(meId) }"
                >
                  <div class="msg-avatar-wrap">
                    <div v-if="showSenderName" class="msg-sender-name">{{ senderLabel(m) }}</div>
                    <el-avatar class="msg-avatar" :size="34" :src="avatarBySender(m)">
                      {{ initialBySender(m) }}
                    </el-avatar>
                  </div>
                  <div class="msg-bubble">
                    <div class="msg-content">{{ m.content }}</div>
                    <div class="msg-time">{{ formatTime(m.createdAt) }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="chat-footer">
              <el-input
                v-model="draft"
                type="textarea"
                :rows="3"
                resize="none"
                maxlength="2000"
                show-word-limit
                placeholder="输入消息，回车发送（Shift+Enter换行）"
                @keydown.enter.prevent="handleEnter"
              />
              <div class="send-row">
                <el-button type="primary" :loading="sending" :disabled="!draft.trim()" @click="send">发送</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="classInfoVisible" :title="classInfoTitle" width="760px">
      <div v-loading="classInfoLoading" style="display: grid; gap: 12px">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="班级名称">{{ classInfo?.name || '—' }}</el-descriptions-item>
          <el-descriptions-item label="班级码">{{ classInfo?.code || '—' }}</el-descriptions-item>
          <el-descriptions-item label="老师">{{ classTeacher?.name || classTeacher?.username || '—' }}</el-descriptions-item>
          <el-descriptions-item label="人数">{{ classMemberRows.length }}</el-descriptions-item>
        </el-descriptions>

        <el-table :data="classMemberRows" border style="width: 100%">
          <el-table-column label="成员" min-width="260">
            <template #default="{ row }">
              <div style="display:flex; align-items:center; gap:10px">
                <el-avatar :size="34" :src="row.avatar || ''">{{ (row.name || row.username || '?').slice(0, 1) }}</el-avatar>
                <div style="min-width:0">
                  <div style="font-weight:800; color:#111827; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:260px">
                    {{ row.name || row.username || row.id }}
                  </div>
                  <div class="mono" style="font-size:12px; color:#6b7280; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:260px">
                    {{ row.roleLabel }} · {{ row.username || '—' }} · {{ row.id }}
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" :disabled="String(row.id) === String(meId)" @click="dmFromMember(row.id)">私信</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="classInfoVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Refresh, Search, UserFilled } from '@element-plus/icons-vue'
import { getAuthToken, getCurrentUser } from '@/utils/authStorage'

const route = useRoute()
const router = useRouter()

const me = ref(getCurrentUser())
const meId = computed(() => String(me.value?.id || ''))
const myRole = computed(() => String(me.value?.role || ''))
const isStudent = computed(() => myRole.value === 'student')

const sidebarTab = ref('conversations')
const convKeyword = ref('')

const conversations = ref([])
const loadingConversations = ref(false)
const activeConversationId = ref('')
const activeConversation = computed(() => conversations.value.find((c) => c.id === activeConversationId.value) || null)
const activeTitle = computed(() => titleOf(activeConversation.value))
const classInfoVisible = ref(false)
const classInfoLoading = ref(false)
const classInfo = ref(null)
const classTeacher = ref(null)
const classStudents = ref([])
const classInfoTitle = computed(() => {
  const name = String(classInfo.value?.name || '').trim() || String(activeTitle.value || '').trim()
  return name ? `${name} · 班级信息` : '班级信息'
})
const classMemberRows = computed(() => {
  const rows = []
  const t = classTeacher.value
  if (t && String(t.id || '').trim()) rows.push({ ...t, roleLabel: '老师' })
  const list = Array.isArray(classStudents.value) ? classStudents.value : []
  for (const s of list) rows.push({ ...s, roleLabel: '学生' })
  return rows
})
const filteredConversations = computed(() => {
  const kw = String(convKeyword.value || '').trim().toLowerCase()
  if (!kw) return conversations.value
  return conversations.value.filter((c) => {
    const t = String(titleOf(c) || '').toLowerCase()
    const p = String(c?.peer?.id || '').toLowerCase()
    const last = String(c?.lastMessage?.content || '').toLowerCase()
    return t.includes(kw) || p.includes(kw) || last.includes(kw)
  })
})

const messages = ref([])
const loadingMessages = ref(false)
const lastMessageId = computed(() => {
  const last = messages.value.length ? messages.value[messages.value.length - 1] : null
  return Number(last?.id || 0)
})
const draft = ref('')
const sending = ref(false)
const msgListRef = ref(null)

const friends = ref([])
const incomingRequests = ref([])
const outgoingRequests = ref([])
const loadingFriends = ref(false)
const addingFriend = ref(false)
const respondingId = ref(0)
const friendSearchText = ref('')
const selectedFriend = ref(null)
const selectedFriendId = computed(() => String(selectedFriend.value?.id || '').trim())

let pollTimer = null
let pollBusy = false
let visibilityHandler = null
const CACHE_CONV_KEY = 'messages:cached_conversations'
const CACHE_ACTIVE_KEY = 'messages:active_conversation'
const CACHE_USER_SEARCH_KEY = 'messages:user_search_cache'
let friendSearchAbort = null
let friendSearchSeq = 0
const userSearchCache = new Map()
let convInFlight = false
let lastConvFetchAt = 0
let convScheduleTimer = null
const CONV_MIN_INTERVAL = 12000

const api = async (path, { method = 'GET', body } = {}) => {
  const token = getAuthToken()
  if (!token) throw new Error('请先登录')
  const headers = { Authorization: `Bearer ${token}` }
  if (method !== 'GET') headers['Content-Type'] = 'application/json'
  const res = await fetch(path, {
    method,
    headers,
    body: method === 'GET' ? undefined : JSON.stringify(body || {})
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok || data?.success === false) throw new Error(data?.detail || data?.message || '请求失败')
  return data
}

const formatTime = (t) => {
  const s = String(t || '')
  if (!s) return ''
  if (s.includes('T')) return s.replace('T', ' ').slice(5, 16)
  return s.length >= 16 ? s.slice(5, 16) : s
}

const titleOf = (c) => {
  if (!c) return ''
  if (c.type === 'class') return c.title || '班级群'
  return c.peer?.name || c.title || '私信'
}

const avatarOf = (c) => (c?.type === 'dm' ? (c.peer?.avatar || '') : '')
const initialOf = (c) => {
  const s = titleOf(c)
  return s ? s.slice(0, 1) : '?'
}

const previewOf = (c) => {
  const text = String(c?.lastMessage?.content || '').trim()
  return text ? text.slice(0, 30) : '暂无消息'
}

const avatarBySender = (m) => {
  const sid = String(m?.senderId || '')
  if (sid && sid === meId.value) return String(me.value?.avatar || '')
  const fromMsg = String(m?.senderAvatar || '')
  if (fromMsg) return fromMsg
  if (activeConversation.value?.type === 'dm') return String(activeConversation.value?.peer?.avatar || '')
  return ''
}

const initialBySender = (m) => {
  const sid = String(m?.senderId || '')
  if (sid && sid === meId.value) return String(me.value?.name || me.value?.username || '?').slice(0, 1)
  const fromMsg = String(m?.senderName || '')
  if (fromMsg) return fromMsg.slice(0, 1)
  if (activeConversation.value?.type === 'dm') return String(activeConversation.value?.peer?.name || '?').slice(0, 1)
  return '?'
}

const showSenderName = computed(() => String(activeConversation.value?.type || '') === 'class')
const senderLabel = (m) => {
  const sid = String(m?.senderId || '')
  if (sid && sid === meId.value) return String(me.value?.name || me.value?.username || '我')
  return String(m?.senderName || m?.senderId || '').trim() || '同学'
}

const scrollToBottom = async () => {
  await nextTick()
  const el = msgListRef.value
  if (!el) return
  el.scrollTop = el.scrollHeight
}

const loadConversations = async ({ force = false } = {}) => {
  if (!getAuthToken()) return
  if (convInFlight) return
  if (!force && Date.now() - lastConvFetchAt < CONV_MIN_INTERVAL) return
  convInFlight = true
  lastConvFetchAt = Date.now()
  loadingConversations.value = true
  try {
    const data = await api(`/api/messages/conversations?t=${Date.now()}`)
    conversations.value = Array.isArray(data?.conversations) ? data.conversations : []
    try {
      sessionStorage.setItem(CACHE_CONV_KEY, JSON.stringify(conversations.value))
    } catch {}
    if (activeConversationId.value && !conversations.value.some((c) => c.id === activeConversationId.value)) {
      activeConversationId.value = ''
      messages.value = []
    }
  } catch (e) {
    ElMessage.error(e?.message || '加载会话失败')
  } finally {
    loadingConversations.value = false
    convInFlight = false
  }
}

const scheduleLoadConversations = (force = false) => {
  if (convScheduleTimer) return
  convScheduleTimer = setTimeout(() => {
    convScheduleTimer = null
    loadConversations({ force })
  }, 220)
}

const loadMessages = async (silent = false) => {
  if (!activeConversationId.value) return
  if (!silent) loadingMessages.value = true
  try {
    const data = await api(`/api/messages/${encodeURIComponent(activeConversationId.value)}?limit=120&t=${Date.now()}`)
    messages.value = Array.isArray(data?.messages) ? data.messages : []
    await api('/api/messages/read', { method: 'POST', body: { conversation_id: activeConversationId.value } })
    scheduleLoadConversations()
    await scrollToBottom()
  } catch (e) {
    ElMessage.error(e?.message || '加载消息失败')
  } finally {
    if (!silent) loadingMessages.value = false
  }
}

const loadNewMessages = async (silent = true) => {
  if (!activeConversationId.value) return
  const afterId = lastMessageId.value
  try {
    const data = await api(`/api/messages/${encodeURIComponent(activeConversationId.value)}?after_id=${afterId}&limit=120&t=${Date.now()}`)
    const incoming = Array.isArray(data?.messages) ? data.messages : []
    if (incoming.length) {
      const existed = new Set(messages.value.map((m) => Number(m.id)))
      for (const m of incoming) {
        const id = Number(m?.id || 0)
        if (!id || existed.has(id)) continue
        messages.value.push(m)
      }
      await api('/api/messages/read', { method: 'POST', body: { conversation_id: activeConversationId.value } })
      scheduleLoadConversations()
      await scrollToBottom()
    }
  } catch (e) {
    if (!silent) ElMessage.error(e?.message || '加载消息失败')
  }
}

const openConversation = async (c) => {
  if (!c?.id) return
  activeConversationId.value = c.id
  try {
    sessionStorage.setItem(CACHE_ACTIVE_KEY, String(c.id))
  } catch {}
  await loadMessages()
}

const send = async () => {
  const text = String(draft.value || '').trim()
  if (!text || !activeConversationId.value) return
  sending.value = true
  try {
    const optimisticId = Date.now()
    messages.value.push({
      id: optimisticId,
      conversationId: activeConversationId.value,
      senderId: meId.value,
      content: text,
      createdAt: new Date().toISOString()
    })
    draft.value = ''
    await scrollToBottom()
    await api('/api/messages/send', { method: 'POST', body: { conversation_id: activeConversationId.value, content: text } })
    messages.value = messages.value.filter((m) => Number(m.id) !== optimisticId)
    await loadNewMessages(true)
    scheduleLoadConversations()
  } catch (e) {
    ElMessage.error(e?.message || '发送失败')
  } finally {
    sending.value = false
  }
}

const handleEnter = (e) => {
  if (e.shiftKey) {
    draft.value += '\n'
    return
  }
  send()
}

const loadFriends = async () => {
  if (!isStudent.value) return
  loadingFriends.value = true
  try {
    const [listRes, reqRes] = await Promise.all([
      api(`/api/friends/list?t=${Date.now()}`),
      api(`/api/friends/requests?t=${Date.now()}`)
    ])
    friends.value = Array.isArray(listRes?.friends) ? listRes.friends : []
    incomingRequests.value = Array.isArray(reqRes?.incoming) ? reqRes.incoming : []
    outgoingRequests.value = Array.isArray(reqRes?.outgoing) ? reqRes.outgoing : []
  } catch (e) {
    ElMessage.error(e?.message || '加载好友失败')
  } finally {
    loadingFriends.value = false
  }
}

const clearFriendSelection = () => {
  friendSearchText.value = ''
  selectedFriend.value = null
}

const sendFriendRequestTo = async (uid) => {
  const toId = String(uid || '').trim()
  if (!toId) return
  addingFriend.value = true
  try {
    await api('/api/friends/request', { method: 'POST', body: { to_user_id: toId } })
    clearFriendSelection()
    ElMessage.success('已发送申请')
    await loadFriends()
  } catch (e) {
    ElMessage.error(e?.message || '发送失败')
  } finally {
    addingFriend.value = false
  }
}

const sendFriendRequestSelected = () => sendFriendRequestTo(selectedFriendId.value)

const queryFriendSuggestions = async (queryString, cb) => {
  const q = String(queryString || '').trim()
  if (q.length < 2) {
    cb([])
    return
  }
  if (/[a-zA-Z]/.test(q) && q.length < 3) {
    cb([])
    return
  }
  const cacheKey = q.toLowerCase()
  const cached = userSearchCache.get(cacheKey)
  if (cached) {
    cb(cached)
    return
  }
  const token = getAuthToken()
  if (!token) {
    cb([])
    return
  }
  if (friendSearchAbort) {
    try { friendSearchAbort.abort() } catch {}
  }
  friendSearchAbort = new AbortController()
  const seq = ++friendSearchSeq
  const traceId = `${Date.now()}-${seq}`
  const t0 = performance.now()
  try {
    const res = await fetch(`/api/users/search?q=${encodeURIComponent(q)}&limit=8&t=${Date.now()}`, {
      headers: { Authorization: `Bearer ${token}`, 'X-Trace-Id': traceId },
      cache: 'no-store',
      signal: friendSearchAbort.signal
    })
    const data = await res.json().catch(() => ({}))
    if (seq !== friendSearchSeq) {
      cb([])
      return
    }
    if (!res.ok || data?.success === false) {
      cb([])
      return
    }
    const existed = new Set((friends.value || []).map((x) => String(x?.id || '')))
    const pending = new Set((outgoingRequests.value || []).filter((r) => r?.status === 'pending').map((r) => String(r?.toUserId || '')))
    const list = (Array.isArray(data?.users) ? data.users : [])
      .filter((u) => {
        const id = String(u?.id || '')
        if (!id) return false
        if (id === meId.value) return false
        if (existed.has(id)) return false
        if (pending.has(id)) return false
        return true
      })
      .map((u) => ({
        value: `${u.name || u.username}（${u.username}）`,
        id: u.id,
        name: u.name || u.username,
        username: u.username,
        avatar: u.avatar || ''
      }))
    userSearchCache.set(cacheKey, list)
    cb(list)
  } catch {
    cb([])
  }
}

const handleFriendSelect = (item) => {
  selectedFriend.value = item || null
}

const respondRequest = async (requestId, action) => {
  respondingId.value = Number(requestId || 0)
  try {
    await api('/api/friends/respond', { method: 'POST', body: { request_id: requestId, action } })
    await loadFriends()
  } catch (e) {
    ElMessage.error(e?.message || '操作失败')
  } finally {
    respondingId.value = 0
  }
}

const startDm = async (uid) => {
  const to = String(uid || '').trim()
  if (!to) return
  try {
    const data = await api('/api/messages/open-dm', { method: 'POST', body: { to_user_id: to, content: '' } })
    await loadConversations({ force: true })
    const cid = String(data?.conversation_id || '')
    if (cid) {
      const target = conversations.value.find((c) => c.id === cid)
      if (target) await openConversation(target)
      else activeConversationId.value = cid
    }
    sidebarTab.value = 'conversations'
  } catch (e) {
    ElMessage.error(e?.message || '无法发起私信')
  }
}

const loadClassInfo = async () => {
  const clsId = String(activeConversation.value?.classId || '').trim()
  if (!clsId) return
  if (classInfoLoading.value) return
  classInfoLoading.value = true
  try {
    const data = await api(`/api/classes/${encodeURIComponent(clsId)}/members?limit=500&t=${Date.now()}`)
    classInfo.value = data?.class || null
    classTeacher.value = data?.teacher || null
    classStudents.value = Array.isArray(data?.students) ? data.students : []
  } catch (e) {
    ElMessage.error(e?.message || '加载班级信息失败')
    classInfo.value = null
    classTeacher.value = null
    classStudents.value = []
  } finally {
    classInfoLoading.value = false
  }
}

const openClassInfo = async () => {
  if (String(activeConversation.value?.type || '') !== 'class') return
  classInfoVisible.value = true
  await loadClassInfo()
}

const dmFromMember = async (uid) => {
  await startDm(uid)
  classInfoVisible.value = false
}

const refreshAll = async () => {
  await loadConversations({ force: true })
  if (sidebarTab.value === 'friends') await loadFriends()
  if (activeConversationId.value) await loadNewMessages(false)
}

const syncUser = () => {
  me.value = getCurrentUser()
  if (!getAuthToken()) {
    conversations.value = []
    friends.value = []
    incomingRequests.value = []
    outgoingRequests.value = []
    activeConversationId.value = ''
    messages.value = []
    return
  }
  refreshAll()
}

onMounted(async () => {
  try {
    const cached = sessionStorage.getItem(CACHE_CONV_KEY)
    if (cached) {
      const parsed = JSON.parse(cached)
      if (Array.isArray(parsed)) conversations.value = parsed
    }
    const cachedSearch = sessionStorage.getItem(CACHE_USER_SEARCH_KEY)
    if (cachedSearch) {
      const parsedSearch = JSON.parse(cachedSearch)
      if (Array.isArray(parsedSearch)) {
        for (const it of parsedSearch) {
          if (it?.k && Array.isArray(it?.v)) userSearchCache.set(String(it.k), it.v)
        }
      }
    }
    const cachedActive = sessionStorage.getItem(CACHE_ACTIVE_KEY)
    if (cachedActive) activeConversationId.value = String(cachedActive || '')
  } catch {}

  syncUser()
  window.addEventListener('user-updated', syncUser)

  pollTimer = setInterval(() => {
    if (!getAuthToken()) return
    if (pollBusy) return
    if (typeof document !== 'undefined' && document.hidden) return
    pollBusy = true
    Promise.resolve()
      .then(() => loadConversations())
      .then(() => {
        if (activeConversationId.value) return loadNewMessages(true)
      })
      .finally(() => {
        pollBusy = false
      })
  }, 6000)

  visibilityHandler = () => {
    if (typeof document === 'undefined') return
    if (!document.hidden) refreshAll()
  }
  document.addEventListener('visibilitychange', visibilityHandler)

  const to = String(route.query?.to || '').trim()
  if (to) {
    await startDm(to)
    router.replace({ path: '/messages', query: {} })
  } else if (activeConversationId.value) {
    const target = conversations.value.find((c) => c.id === activeConversationId.value)
    if (target) await loadMessages(true)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('user-updated', syncUser)
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = null
  if (convScheduleTimer) clearTimeout(convScheduleTimer)
  convScheduleTimer = null
  if (visibilityHandler) document.removeEventListener('visibilitychange', visibilityHandler)
  visibilityHandler = null
  try {
    const pairs = Array.from(userSearchCache.entries()).slice(0, 20).map(([k, v]) => ({ k, v }))
    sessionStorage.setItem(CACHE_USER_SEARCH_KEY, JSON.stringify(pairs))
  } catch {}
})

watch(sidebarTab, (v) => {
  if (v === 'friends') loadFriends()
})
</script>

<style scoped>
.wx-page {
  min-height: calc(100vh - 60px);
  background: linear-gradient(180deg, #f3f4f6 0%, #eef2f7 100%);
}

.wx-container {
  max-width: 1300px;
  margin: 0 auto;
  padding: 14px 14px 22px;
}

.wx-shell {
  height: calc(100vh - 60px - 36px);
  min-height: 720px;
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgba(17, 24, 39, 0.08);
  box-shadow: 0 20px 60px rgba(17, 24, 39, 0.08);
  display: grid;
  grid-template-columns: 72px 320px 1fr;
}

.wx-rail {
  background: #1f2937;
  color: #e5e7eb;
  display: grid;
  grid-template-rows: auto 1fr auto;
  align-items: start;
  padding: 12px 10px;
  gap: 14px;
}

.rail-avatar {
  justify-self: center;
  border: 2px solid rgba(255, 255, 255, 0.18);
}

.rail-nav {
  display: grid;
  gap: 8px;
  justify-items: center;
  align-content: start;
}

.rail-bottom {
  display: grid;
  justify-items: center;
  gap: 8px;
}

.rail-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.04);
  color: #e5e7eb;
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: transform 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}

.rail-btn:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}

.rail-btn.active {
  background: rgba(99, 102, 241, 0.22);
  border-color: rgba(99, 102, 241, 0.35);
  color: #fff;
}

.rail-btn.subtle {
  background: transparent;
  border-color: transparent;
}

.wx-list {
  background: rgba(249, 250, 251, 0.9);
  border-right: 1px solid rgba(17, 24, 39, 0.08);
  display: grid;
  grid-template-rows: auto 1fr;
}

.list-top {
  padding: 14px 12px 12px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
  display: grid;
  gap: 10px;
}

.list-title {
  font-weight: 900;
  color: #111827;
  font-size: 16px;
}

.search :deep(.el-input__wrapper) {
  border-radius: 12px;
}

.friend-tools {
  display: grid;
  grid-template-columns: 1fr 86px;
  gap: 8px;
  align-items: center;
}

.friend-search :deep(.el-input__wrapper) {
  border-radius: 12px;
}

.suggest-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 6px;
}

.suggest-meta {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.suggest-name {
  font-weight: 900;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}

.suggest-sub {
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}

.list-body {
  overflow: auto;
  padding: 10px;
}

.conv-list {
  display: grid;
  gap: 8px;
}

.conv-item {
  border: 1px solid rgba(17, 24, 39, 0.06);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  padding: 10px 10px;
  display: grid;
  grid-template-columns: 48px 1fr;
  gap: 12px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.conv-item.active {
  background: #fff;
  border-color: rgba(99, 102, 241, 0.28);
}

.conv-main {
  display: grid;
  gap: 4px;
}

.conv-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.conv-name {
  font-weight: 900;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-time {
  font-size: 12px;
  color: #6b7280;
  flex: none;
}

.conv-preview {
  font-size: 12px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wx-chat {
  background: #fff;
  display: grid;
}

.chat-empty {
  display: grid;
  place-items: center;
}

.chat-panel {
  display: grid;
  grid-template-rows: auto 1fr auto;
  min-width: 0;
}

.chat-header {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.chat-header-left {
  min-width: 0;
}

.chat-name {
  font-weight: 900;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-sub {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.chat-body {
  padding: 16px;
  overflow: auto;
  background: linear-gradient(180deg, rgba(245, 247, 250, 0.7) 0%, rgba(233, 236, 241, 0.7) 100%);
}

.msg-list {
  display: grid;
  gap: 10px;
}

.msg-row {
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: 12px;
  align-items: end;
}

.msg-row.mine {
  grid-template-columns: 1fr 60px;
}

.msg-avatar-wrap {
  display: grid;
  justify-items: center;
  gap: 4px;
  align-content: end;
}

.msg-sender-name {
  font-size: 12px;
  color: #6b7280;
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1;
}

.msg-row.mine .msg-avatar-wrap {
  order: 2;
}

.msg-row.mine .msg-bubble {
  justify-self: end;
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.16);
}

.msg-bubble {
  max-width: 560px;
  background: #fff;
  border: 1px solid rgba(17, 24, 39, 0.08);
  border-radius: 12px;
  padding: 10px 12px;
  display: grid;
  gap: 6px;
}

.msg-content {
  color: #111827;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-time {
  font-size: 12px;
  color: #6b7280;
}

.chat-footer {
  padding: 12px 16px 14px;
  border-top: 1px solid rgba(17, 24, 39, 0.08);
  display: grid;
  gap: 10px;
}

.send-row {
  display: flex;
  justify-content: flex-end;
}

.friend-section {
  margin-top: 12px;
}

.section-h {
  font-weight: 900;
  color: #111827;
  margin-bottom: 8px;
  margin-top: 2px;
  font-size: 13px;
}

.mt {
  margin-top: 16px;
}

.req-list {
  display: grid;
  gap: 8px;
}

.req-item {
  border: 1px solid rgba(17, 24, 39, 0.06);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.req-user {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.req-meta {
  min-width: 0;
}

.req-name {
  font-weight: 900;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}

.req-id {
  color: #6b7280;
  font-size: 12px;
}

.req-actions {
  display: flex;
  gap: 8px;
  flex: none;
}

.req-status {
  font-size: 12px;
  color: #6b7280;
}

.friend-list {
  display: grid;
  gap: 8px;
}

.friend-item {
  width: 100%;
  border: 1px solid rgba(17, 24, 39, 0.06);
  background: rgba(255, 255, 255, 0.92);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-align: left;
}

.friend-meta {
  min-width: 0;
}

.friend-name {
  font-weight: 900;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
}

.friend-id {
  font-size: 12px;
  color: #6b7280;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

@media (max-width: 980px) {
  .wx-shell {
    grid-template-columns: 64px 1fr;
  }
  .wx-chat {
    display: none;
  }
}
</style>

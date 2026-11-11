<template>
  <div class="leaderboard-page">
    <div class="hero">
      <div class="hero-inner">
        <div class="hero-left">
          <h1>排行榜</h1>
          <p>按通过题数（去重）统计，累计所有历史记录</p>
        </div>
        <div class="hero-right">
          <el-button plain :loading="loading" @click="load">刷新</el-button>
        </div>
      </div>
    </div>

    <div class="container">
      <el-card shadow="hover" class="podium-card">
        <div class="podium-title">Top 3</div>
        <div class="podium">
          <div class="podium-item">
            <div class="podium-head clickable" @click="openUserFromRow(podium.second, $event)" role="button" tabindex="0" @keydown.enter="openUserFromRow(podium.second, $event)" @keydown.space.prevent="openUserFromRow(podium.second, $event)">
              <el-avatar :size="44" :src="podium.second?.avatar || ''">{{ getInitial(podium.second?.name) }}</el-avatar>
              <div class="podium-name">{{ podium.second?.name || '空位' }}</div>
            </div>
            <div class="podium-bar-wrap">
              <div class="podium-bar second-bar" :style="barStyle(podium.second)"><span class="podium-glyph" aria-hidden="true">02</span><i class="podium-light" aria-hidden="true"></i></div>
              <div class="podium-score">{{ formatScore(podium.second) }}</div>
              <div class="podium-rank">第2</div>
            </div>
          </div>

          <div class="podium-item first">
            <div class="podium-head clickable" @click="openUserFromRow(podium.first, $event)" role="button" tabindex="0" @keydown.enter="openUserFromRow(podium.first, $event)" @keydown.space.prevent="openUserFromRow(podium.first, $event)">
              <el-avatar :size="52" :src="podium.first?.avatar || ''">{{ getInitial(podium.first?.name) }}</el-avatar>
              <div class="podium-name">{{ podium.first?.name || '空位' }}</div>
            </div>
            <div class="podium-bar-wrap">
              <div class="podium-bar first-bar" :style="barStyle(podium.first)"><span class="podium-glyph" aria-hidden="true">01</span><i class="podium-light" aria-hidden="true"></i></div>
              <div class="podium-score">{{ formatScore(podium.first) }}</div>
              <div class="podium-rank">第1</div>
            </div>
          </div>

          <div class="podium-item">
            <div class="podium-head clickable" @click="openUserFromRow(podium.third, $event)" role="button" tabindex="0" @keydown.enter="openUserFromRow(podium.third, $event)" @keydown.space.prevent="openUserFromRow(podium.third, $event)">
              <el-avatar :size="44" :src="podium.third?.avatar || ''">{{ getInitial(podium.third?.name) }}</el-avatar>
              <div class="podium-name">{{ podium.third?.name || '空位' }}</div>
            </div>
            <div class="podium-bar-wrap">
              <div class="podium-bar third-bar" :style="barStyle(podium.third)"><span class="podium-glyph" aria-hidden="true">03</span><i class="podium-light" aria-hidden="true"></i></div>
              <div class="podium-score">{{ formatScore(podium.third) }}</div>
              <div class="podium-rank">第3</div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card shadow="hover" class="card">
        <el-skeleton v-if="loading && rows.length === 0" :rows="10" animated />
        <el-empty v-else-if="!loading && rows.length === 0" description="暂无排行数据" />
        <el-empty v-else-if="!loading && listRows.length === 0" description="暂无更多排行数据" />
        <el-table
          v-else
          :data="listRows"
          stripe
          style="width: 100%"
          :row-class-name="rowClassName"
        >
          <el-table-column prop="rank" label="排名" width="80" />
          <el-table-column label="用户" min-width="220">
            <template #default="{ row }">
              <div class="user-cell clickable" @click="openUserFromRow(row, $event)" role="button" tabindex="0" @keydown.enter="openUserFromRow(row, $event)" @keydown.space.prevent="openUserFromRow(row, $event)">
                <el-avatar :size="34" :src="row.avatar || ''">{{ (row.name || '').slice(0, 1) }}</el-avatar>
                <div class="user-meta">
                  <div class="user-name">{{ row.name || '未命名' }}</div>
                  <div class="user-id">ID：{{ row.userId }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="passedUnique" label="通过题数" width="110" />
          <el-table-column prop="successRuns" label="成功运行" width="110" />
          <el-table-column prop="totalRuns" label="总运行" width="100" />
          <el-table-column prop="points" label="积分" width="90" />
        </el-table>
      </el-card>

      <el-dialog v-model="detailVisible" title="用户信息" width="520px" class="motion-morph-dialog" @open="detailMotion.open" @close="closeUserDetail">
        <div v-if="detail" class="detail">
          <div class="detail-head">
            <el-avatar ref="detailAvatar" :size="56" :src="detail.user?.avatar || ''">{{ getInitial(detail.user?.name) }}</el-avatar>
            <div class="detail-meta">
              <div class="detail-name">{{ detail.user?.name || '未命名' }}</div>
              <div class="detail-sub mono">ID：{{ detail.user?.id }}</div>
              <div class="detail-sub muted" v-if="detail.user?.created_at">注册：{{ formatCreatedAt(detail.user?.created_at) }}</div>
            </div>
          </div>

          <el-skeleton v-if="detailLoading" :rows="3" animated /><div v-else class="detail-grid">
            <div class="metric">
              <div class="metric-k">刷题数量</div>
              <div class="metric-v">{{ Number(detail.stats?.passed_unique || 0) }}</div>
            </div>
            <div class="metric">
              <div class="metric-k">成功运行</div>
              <div class="metric-v">{{ Number(detail.stats?.success_runs || 0) }}</div>
            </div>
            <div class="metric">
              <div class="metric-k">总运行</div>
              <div class="metric-v">{{ Number(detail.stats?.total_runs || 0) }}</div>
            </div>
            <div class="metric">
              <div class="metric-k">积分</div>
              <div class="metric-v">{{ Number(detail.points || 0) }}</div>
            </div>
          </div>
        </div>
        <template #footer>
          <el-button v-if="canDmDetail" plain @click="goMessage">私信</el-button>
          <el-button v-if="canAddFriendDetail" type="primary" :loading="addingFriend" :disabled="friendRequestSent" @click="addFriend">
            {{ friendRequestSent ? '已发送' : '加好友' }}
          </el-button>
          <el-button @click="detailVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </div>

    <WhitespaceGame scene="trophy" game="lights" />
  </div>
</template>

<script setup>
import {useDialogMorph} from '@/composables/useDialogMorph'
import WhitespaceGame from '@/components/WhitespaceGame.vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAuthToken, getCurrentUser } from '@/utils/authStorage'

const router = useRouter()

const rows = ref([])
const loading = ref(false)
const meId = ref(String(getCurrentUser()?.id || ''))

const podium = computed(() => {
  const first = rows.value[0] || null
  const second = rows.value[1] || null
  const third = rows.value[2] || null
  const maxPassed = Math.max(
    Number(first?.passedUnique || 0),
    Number(second?.passedUnique || 0),
    Number(third?.passedUnique || 0),
    0
  )
  return { first, second, third, maxPassed: maxPassed > 0 ? maxPassed : 1 }
})

const listRows = computed(() => rows.value.slice(3))

const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const canAddFriendDetail = computed(() => {
  const to = String(detail.value?.user?.id || '').trim()
  const me = String(meId.value || '').trim()
  return !!to && !!me && to !== me
})
const canDmDetail = canAddFriendDetail
const addingFriend = ref(false)
const sentFriendRequests = new Set()
const friendRequestSent = computed(() => {
  const to = String(detail.value?.user?.id || '').trim()
  return !!to && sentFriendRequests.has(to)
})

const rowClassName = ({ row }) => {
  if (!meId.value) return ''
  return String(row?.userId || '') === String(meId.value) ? 'me-row' : ''
}

const getInitial = (name) => {
  const s = String(name || '').trim()
  return s ? s.slice(0, 1) : '?'
}

const formatScore = (row) => {
  if (!row) return '-'
  const n = Number(row?.passedUnique || 0)
  return Number.isFinite(n) ? String(n) : '0'
}

const barStyle = (row) => {
  const maxH = 200
  const minH = 42
  if (!row) return { height: `${minH}px` }
  const val = Number(row?.passedUnique || 0)
  const ratio = Math.max(0, Math.min(1, val / podium.value.maxPassed))
  const h = Math.round(minH + (maxH - minH) * ratio)
  return { height: `${h}px` }
}

const formatCreatedAt = (t) => {
  const s = String(t || '')
  if (!s) return ''
  if (s.includes('T')) return s.replace('T', ' ').slice(0, 16)
  return s.length >= 16 ? s.slice(0, 16) : s
}

let detailGeneration=0
const detailOrigin=ref(null),detailAvatar=ref(null)
const detailMotion=useDialogMorph({source:()=>detailOrigin.value,target:()=>detailAvatar.value?.$el,round:true})
function closeUserDetail(){detailGeneration++;detailLoading.value=false;detailMotion.close()}
const openUserFromRow = async (row, event) => {
  const uid = String(row?.userId || row?.id || row?.user?.id || '').trim()
  if (!uid) return
  const generation=++detailGeneration
  detailOrigin.value=event?.currentTarget?.querySelector('.el-avatar') || event?.currentTarget
  detailVisible.value = true
  detailLoading.value = true
  detail.value = {
    user: {
      id: uid,
      name: String(row?.name || ''),
      avatar: String(row?.avatar || ''),
      created_at: ''
    },
    stats: {
      total_runs: Number(row?.totalRuns || 0),
      success_runs: Number(row?.successRuns || 0),
      passed_unique: Number(row?.passedUnique || 0)
    },
    points: Number(row?.points || 0)
  }
  try {
    const res = await fetch(`/api/users/public/${encodeURIComponent(uid)}?t=${Date.now()}`, { cache: 'no-store' })
    const data = await res.json().catch(() => ({}))
    if (generation===detailGeneration && res.ok && data?.success) {
      detail.value = {
        user: data.user || detail.value.user,
        stats: data.stats || detail.value.stats,
        points: Number(data.points || 0)
      }
    }
  } catch {}
  finally {
    if(generation===detailGeneration)detailLoading.value = false
  }
}

const addFriend = async () => {
  const to = String(detail.value?.user?.id || '').trim()
  if (!to) return
  const token = getAuthToken()
  if (!token) {
    ElMessage.error('请先登录')
    return
  }
  addingFriend.value = true
  try {
    const res = await fetch('/api/friends/request', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ to_user_id: to })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '发送失败')
    }
    sentFriendRequests.add(to)
    ElMessage.success('已发送申请')
  } catch (e) {
    ElMessage.error(e?.message || '发送失败')
  } finally {
    addingFriend.value = false
  }
}

const goMessage = () => {
  const to = String(detail.value?.user?.id || '').trim()
  if (!to) return
  detailVisible.value = false
  router.push({ path: '/messages', query: { to } })
}

const load = async () => {
  loading.value = true
  try {
    const res = await fetch(`/api/leaderboard?limit=50&t=${Date.now()}`, { cache: 'no-store' })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.message || data?.detail || '加载失败')
    }
    rows.value = Array.isArray(data?.leaderboard) ? data.leaderboard : []
  } catch (e) {
    ElMessage.error(e?.message || '加载排行榜失败')
    rows.value = []
  } finally {
    loading.value = false
  }
}

const syncUser = () => {
  meId.value = String(getCurrentUser()?.id || '')
}

onMounted(() => {
  syncUser()
  window.addEventListener('user-updated', syncUser)
  load()
})

onBeforeUnmount(() => {
  window.removeEventListener('user-updated', syncUser)
})
</script>

<style scoped>
.leaderboard-page {
  min-height: calc(100vh - 60px);
  background: linear-gradient(180deg, #f5f7fa 0%, #e8ecf1 100%);
}

.hero {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 36px 16px;
  color: #fff;
}

.hero-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.hero-left h1 {
  margin: 0;
  font-size: 38px;
  font-weight: 800;
}

.hero-left p {
  margin: 10px 0 0;
  opacity: 0.92;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 18px 16px 28px;
  display: grid;
  gap: 14px;
}

.card {
  border-radius: 14px;
}

.podium-card {
  border-radius: 14px;
}

.podium-title {
  font-weight: 900;
  color: #111827;
  margin-bottom: 10px;
}

.clickable {
  cursor: pointer;
}

.clickable:hover .user-name,
.clickable:hover .podium-name {
  text-decoration: underline;
  text-decoration-color: rgba(17, 24, 39, 0.35);
}

.podium {
  display: grid;
  grid-template-columns: 1fr 1.2fr 1fr;
  gap: 14px;
  align-items: end;
}

.podium-item {
  display: grid;
  gap: 10px;
  align-items: end;
  justify-items: center;
  cursor: default;
  transition: filter 0.18s ease;
  position: relative;
}

.podium-item.first {
  transform: translateY(-4px);
}

.podium-item:hover {
  filter: drop-shadow(0 10px 18px rgba(0, 0, 0, 0.12));
}

.podium-head {
  display: grid;
  gap: 6px;
  justify-items: center;
  will-change: transform;
  position: relative;
  z-index: 3;
}

.podium-name {
  max-width: 160px;
  font-weight: 900;
  color: #111827;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.podium-bar-wrap {
  width: 100%;
  max-width: 220px;
  display: grid;
  justify-items: center;
  align-items: end;
  gap: 8px;
  padding-top: 10px;
  position: relative;
  z-index: 1;
}

.podium-item.first .podium-bar-wrap {
  padding-top: 18px;
}

.podium-score {
  font-size: 14px;
  font-weight: 900;
  color: #111827;
  will-change: transform;
  position: relative;
  z-index: 4;
  margin-top: 2px;
}

.podium-bar {
  width: 100%;
  border-radius: 12px 12px 10px 10px;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.85) 0%, rgba(124, 58, 237, 0.85) 100%);
  border: 1px solid rgba(17, 24, 39, 0.08);
  transform-origin: bottom center;
  transition: filter 0.18s ease, box-shadow 0.18s ease;
  will-change: transform;
  position: relative;
  z-index: 1;
}

.podium-item:hover .podium-bar {
  animation: podium-bounce 420ms cubic-bezier(0.2, 0.9, 0.2, 1) both;
  filter: brightness(1.06);
  box-shadow: 0 14px 22px rgba(17, 24, 39, 0.16);
}

.podium-item:hover .podium-head {
  animation: podium-head-float 420ms cubic-bezier(0.2, 0.9, 0.2, 1) both;
}

.podium-item:hover .podium-score {
  animation: podium-score-float 420ms cubic-bezier(0.2, 0.9, 0.2, 1) both;
}

.podium-bar.base {
  background: linear-gradient(180deg, rgba(96, 165, 250, 0.8) 0%, rgba(59, 130, 246, 0.8) 100%);
}

.podium-bar.second-bar {
  background: linear-gradient(180deg, rgba(34, 197, 94, 0.86) 0%, rgba(16, 185, 129, 0.86) 100%);
}

.podium-bar.first-bar {
  background: linear-gradient(180deg, rgba(245, 158, 11, 0.9) 0%, rgba(249, 115, 22, 0.9) 100%);
}

.podium-bar.third-bar {
  background: linear-gradient(180deg, rgba(168, 85, 247, 0.86) 0%, rgba(236, 72, 153, 0.86) 100%);
}

.podium-item:hover .podium-bar.first-bar {
  box-shadow: 0 14px 22px rgba(249, 115, 22, 0.18);
}

.podium-item:hover .podium-bar.second-bar {
  box-shadow: 0 14px 22px rgba(16, 185, 129, 0.18);
}

.podium-item:hover .podium-bar.third-bar {
  box-shadow: 0 14px 22px rgba(236, 72, 153, 0.18);
}

@keyframes podium-bounce {
  0% { transform: scale3d(1, 1, 1); }
  55% { transform: scale3d(1.03, 1.10, 1); }
  78% { transform: scale3d(1.03, 1.05, 1); }
  100% { transform: scale3d(1.03, 1.08, 1); }
}

@keyframes podium-head-float {
  0% { transform: translate3d(0, 0, 0) scale3d(1, 1, 1); }
  55% { transform: translate3d(0, -10px, 0) scale3d(1.02, 1.02, 1); }
  78% { transform: translate3d(0, -6px, 0) scale3d(1.01, 1.01, 1); }
  100% { transform: translate3d(0, -8px, 0) scale3d(1.015, 1.015, 1); }
}

@keyframes podium-score-float {
  0% { transform: translate3d(0, 0, 0); }
  55% { transform: translate3d(0, -4px, 0); }
  78% { transform: translate3d(0, -2px, 0); }
  100% { transform: translate3d(0, -3px, 0); }
}

.podium-rank {
  font-size: 12px;
  color: #6b7280;
  position: relative;
  z-index: 4;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-meta {
  display: grid;
  gap: 2px;
}

.user-name {
  font-weight: 800;
  color: #111827;
}

.user-id {
  font-size: 12px;
  color: #6b7280;
}

:deep(.me-row) {
  background: rgba(255, 215, 0, 0.12) !important;
}

.detail {
  display: grid;
  gap: 14px;
}

.detail-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-meta {
  display: grid;
  gap: 4px;
}

.detail-name {
  font-size: 18px;
  font-weight: 900;
  color: #111827;
}

.detail-sub {
  font-size: 12px;
}

.muted {
  color: #6b7280;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.metric {
  background: rgba(17, 24, 39, 0.03);
  border: 1px solid rgba(17, 24, 39, 0.06);
  border-radius: 10px;
  padding: 10px;
  display: grid;
  gap: 6px;
}

.metric-k {
  font-size: 12px;
  color: #6b7280;
  font-weight: 800;
}

.metric-v {
  font-size: 18px;
  font-weight: 900;
  color: #111827;
}

@media (max-width: 600px) {
  .detail-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
.podium { padding: 15px 20px 4px 4px; perspective: 1100px; }
.podium-card { overflow: visible; background: linear-gradient(130deg,#fff,#faf7fd); }
.podium-bar { --podium-depth: 14px; --podium-rise: 12px; border: 0; border-radius: 0 0 0 8px; transition: height 750ms cubic-bezier(.2,.75,.25,1),filter 180ms,box-shadow 180ms; box-shadow: -6px 12px 25px #9271b422; transform-style: preserve-3d; }
/* All three faces share the same projection vector: (depth, -rise). */
.podium-bar::before { content: ''; position: absolute; left: 0; right: calc(-1 * var(--podium-depth)); top: calc(-1 * var(--podium-rise)); height: var(--podium-rise); background: #b4e6cb; clip-path: polygon(0 100%,calc(100% - var(--podium-depth)) 100%,100% 0,var(--podium-depth) 0); pointer-events: none; }
.podium-bar::after { content: ''; position: absolute; top: calc(-1 * var(--podium-rise)); bottom: 0; right: calc(-1 * var(--podium-depth)); width: calc(var(--podium-depth) + 1px); background: linear-gradient(180deg,#43ad89,#279572); clip-path: polygon(0 var(--podium-rise),100% 0,100% calc(100% - var(--podium-rise)),0 100%); pointer-events: none; }
.podium-bar.first-bar::before { background: #e4d4ad; }.podium-bar.first-bar::after { background: linear-gradient(180deg,#c9b583,#ae9161); }
.podium-bar.third-bar::before { background: #d7bdd4; }.podium-bar.third-bar::after { background: linear-gradient(180deg,#b994b5,#967693); }
.podium-glyph { position: absolute; inset: 0; display: grid; place-items: center; font: 300 clamp(30px,5vw,64px) Consolas,monospace; color: #ffffffe0; opacity: .4; text-shadow: 0 2px 8px #56407422; pointer-events: none; }
.podium-light { position: absolute; inset: 4px 8px; border-radius: 6px; background: linear-gradient(120deg,transparent 25%,#fff4 49%,transparent 70%); background-size: 260% 100%; animation: podium-light 8s ease-in-out infinite; pointer-events: none; }
.podium-item:nth-child(2) .podium-light { animation-delay: -2s; }.podium-item:nth-child(3) .podium-light { animation-delay: -4s; }
@keyframes podium-light { 0%,30% { background-position: 170% 0; opacity: 0; }45%,70% { opacity: .8; }100% { background-position: -70% 0; opacity: 0; } }
@media(max-width:640px){.podium{gap:16px;padding-right:13px}.podium-bar{--podium-depth:10px;--podium-rise:8px}.podium-glyph{font-size:32px}}
</style>

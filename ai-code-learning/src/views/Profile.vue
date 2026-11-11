<template>
  <div class="profile-page">
    <div class="profile-container">
      <header class="profile-header"><button class="profile-motion-back" @click="backFromProfile">← 返回</button><div><h1>个人中心</h1><p>记录学习进步，继续你喜欢的课程。</p></div><span v-if="isLogin" class="header-note"><el-icon><Reading /></el-icon> 每一次练习，都是进步</span></header>
      <div v-if="isLogin" class="profile-grid">
        <section class="identity-card">
          <div class="identity-person"><img data-profile-avatar v-if="currentUser?.avatar" :src="currentUser.avatar" class="avatar" alt="用户头像"><span v-else data-profile-avatar class="avatar avatar-initial">{{ displayName.slice(0, 1) || '学' }}</span><div class="user-meta"><div class="identity-name"><h2 class="user-name">{{ displayName }}</h2><span class="badge" :class="roleBadgeClass">{{ roleText }}</span><span class="level-badge">Lv.{{ level }}</span></div><p class="user-sub">用户 ID <span class="mono">{{ form.id }}</span></p></div></div>
          <el-button class="edit-profile-button" plain @click="openProfileEditor"><el-icon><EditPen /></el-icon><span>编辑资料</span></el-button>
        </section>

        <el-card shadow="never" class="profile-card overview-card">
          <div class="section-heading overview-header"><h2 class="section-title">学习概览</h2><el-button size="small" text :loading="loadingOverview" @click="loadOverview"><el-icon><Refresh /></el-icon><span>刷新</span></el-button></div>
          <el-skeleton v-if="loadingOverview" :rows="2" animated />
          <div v-else class="overview-grid">
            <div class="kpi"><div class="kpi-label"><el-icon><Coin /></el-icon>当前积分</div><div class="kpi-value">{{ points }}<small>分</small></div><div class="kpi-sub">学习积累，解锁更多奖励</div></div>
            <div class="kpi"><div class="kpi-label"><el-icon><Calendar /></el-icon>今日签到</div><div class="kpi-value signin-value" :class="{signed: signedToday}">{{ signedToday ? '已签到' : '未签到' }}</div><div class="kpi-sub">已连续签到 {{ consecutiveDays }} 天</div></div>
            <div class="kpi"><div class="kpi-label"><el-icon><CircleCheck /></el-icon>练习正确率</div><div class="kpi-value">{{ successRate }}<small>%</small></div><div class="kpi-sub">累计提交 {{ totalSubmissions }} 次</div></div>
            <div class="kpi"><div class="kpi-label"><el-icon><Reading /></el-icon>通过题目</div><div class="kpi-value">{{ passedUnique }}<small>题</small></div><div class="kpi-sub">成功通过的不同题目</div></div>
            <div class="kpi"><div class="kpi-label"><el-icon><Warning /></el-icon>错题记录</div><div class="kpi-value">{{ totalWrong }}<small>次</small></div><div class="kpi-sub">涉及 {{ distinctWrongProblems }} 道题目</div></div>
          </div>
        </el-card>

        <div class="profile-content">
          <div class="content-main">
            <el-card shadow="never" class="profile-card collections-card">
              <div class="section-heading collections-header"><div class="section-copy"><h2 class="section-title">我的收藏 <span class="collection-count">{{ favoriteCourses.length }}</span></h2><p class="section-caption">随时回看收藏的视频课程</p></div><el-button size="small" text :loading="loadingCollections" @click="loadCollections"><el-icon><Refresh /></el-icon><span>刷新收藏</span></el-button></div>
              <el-alert v-if="collectionsError" :title="collectionsError" type="error" :closable="false" show-icon><template #default><el-button link type="primary" @click="loadCollections">重试</el-button></template></el-alert>
              <el-skeleton v-if="loadingCollections && !favoriteCourses.length" :rows="3" animated />
              <template v-else-if="!collectionsError || favoriteCourses.length">
                <p v-if="unavailableCount" class="muted unavailable-note">部分已收藏课程已下架，下面仅展示仍可观看的视频。</p>
                <div v-if="!favoriteCourses.length" class="favorites-empty"><span class="empty-collection-icon"><el-icon><Collection /></el-icon></span><div><h3>把喜欢的课程收藏起来</h3><p>还没有收藏视频，去学习中心挑选喜欢的课程吧</p><el-button type="primary" size="small" @click="router.push('/learning-center')">去收藏视频<el-icon><ArrowRight /></el-icon></el-button></div></div>
                <div v-else class="favorite-list">
                  <article v-for="course in favoriteCourses" :key="course.id" class="favorite-course"><button class="favorite-cover" :aria-label="`播放${course.name}`" @click="playFavorite(course, $event)"><img :src="course.cover" :alt="course.name" loading="lazy"><span class="favorite-duration">{{ course.duration }}</span><span class="favorite-play" aria-hidden="true"><el-icon><VideoPlay /></el-icon></span></button><div class="favorite-content"><h3>{{ course.name }}</h3><p class="favorite-meta">{{ [course.teacher, course.level].filter(Boolean).join(' · ') }}</p><p class="favorite-desc">{{ course.desc }}</p><div class="favorite-actions"><el-button type="primary" size="small" @click="playFavorite(course, $event)"><el-icon><VideoPlay /></el-icon>播放视频</el-button><el-button size="small" text :loading="removingCourse === String(course.id)" :disabled="!!removingCourse && removingCourse !== String(course.id)" @click="removeFavorite(course)">取消收藏</el-button></div></div></article>
                </div>
              </template>
            </el-card>

            <el-card shadow="never" class="profile-card activity-card">
              <div class="section-heading"><h2 class="section-title">最近运行<span class="section-hint">最近 {{ recentHistory.length }} 条</span></h2><router-link class="more-link" to="/daily-checkin">去练习<el-icon><ArrowRight /></el-icon></router-link></div>
              <div v-if="!recentHistory.length" class="small-empty"><el-icon><Document /></el-icon><p>还没有运行记录，完成一次练习就会出现在这里。</p></div>
              <div v-else class="activity-list"><div v-for="item in recentHistory" :key="item.id" class="activity-item"><span class="language-tag">{{ item.language }}</span><span class="record-title ellipsis" :title="item.problem_id">{{ item.problem_id === 'sandbox' ? '自由练习' : item.problem_id || '编程练习' }}</span><span class="status" :class="item.success ? 'ok' : 'bad'"><i />{{ item.success ? '成功' : '失败' }}</span><time class="muted">{{ formatTime(item.submitted_at) }}</time></div></div>
            </el-card>
          </div>

          <aside class="content-side">
            <el-card shadow="never" class="profile-card quick-card"><div class="section-heading"><h2 class="section-title">常用功能</h2><span class="section-hint">快捷直达</span></div><div class="quick-actions"><router-link class="quick-btn" to="/learning-center"><span class="quick-icon purple"><el-icon><VideoPlay /></el-icon></span><span>学习中心</span></router-link><router-link class="quick-btn" to="/daily-checkin"><span class="quick-icon blue"><el-icon><Calendar /></el-icon></span><span>每日打卡</span></router-link><router-link class="quick-btn" to="/wrong-questions"><span class="quick-icon orange"><el-icon><Document /></el-icon></span><span>错题本</span></router-link><router-link class="quick-btn" to="/points-mall"><span class="quick-icon green"><el-icon><Present /></el-icon></span><span>积分商城</span></router-link><router-link class="quick-btn" to="/competition"><span class="quick-icon blue"><el-icon><Trophy /></el-icon></span><span>班级测试</span></router-link><router-link class="quick-btn" to="/messages"><span class="quick-icon purple"><el-icon><Message /></el-icon></span><span>我的消息</span></router-link></div></el-card>
            <el-card shadow="never" class="profile-card exchange-card"><div class="section-heading"><h2 class="section-title">最近兑换</h2><router-link class="more-link" to="/points-mall">去商城<el-icon><ArrowRight /></el-icon></router-link></div><div v-if="!recentExchanges.length" class="small-empty"><el-icon><Present /></el-icon><p>还没有兑换记录</p><span class="muted">积累积分，兑换心仪的奖励</span></div><div v-else class="exchange-list"><div v-for="r in recentExchanges" :key="r.id" class="exchange-item"><span class="exchange-icon"><el-icon><Present /></el-icon></span><div class="exchange-info"><span class="ellipsis" :title="r.goodsName">{{ r.goodsName }}</span><time class="muted">{{ formatTime(r.time) }}</time></div><div class="exchange-state"><span class="points-cost">-{{ r.points }}分</span><span class="status" :class="exchangeStatusClass(r.status)">{{ exchangeStatusText(r.status) }}</span></div></div></div></el-card>
          </aside>
        </div>
      </div>
      <el-card v-else shadow="never" class="profile-card login-card"><el-empty description="登录后才能查看个人中心"><el-button type="primary" @click="goLogin">去登录</el-button></el-empty></el-card>
    </div>

    <el-drawer v-model="profileEditorOpen" title="编辑个人资料" size="min(440px, 94vw)" append-to-body @closed="reset">
      <div class="editor-avatar"><img :src="form.avatar" class="avatar" alt="头像预览"><div class="avatar-actions"><el-upload :show-file-list="false" :auto-upload="false" accept="image/*" :on-change="handleAvatarChange"><el-button size="small" plain>更换头像</el-button></el-upload><el-button size="small" plain @click="randomAvatar">随机头像</el-button></div></div>
      <div class="form-section"><el-form :model="form" label-position="top"><el-form-item label="昵称"><el-input v-model="form.name" placeholder="请输入昵称" maxlength="30" show-word-limit /></el-form-item><el-form-item label="用户ID"><el-input :model-value="form.id" disabled /></el-form-item><p class="muted editor-hint">修改头像或昵称后，点击保存生效。</p><div class="form-actions"><el-button @click="profileEditorOpen = false">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存修改</el-button></div></el-form></div>
    </el-drawer>
    <CoursePlayer v-model:open="favoritePlayerOpen" :course="favoritePlaying" :resume="favoriteResume" :origin="favoriteOrigin" @progress="saveFavoriteProgress" />
    <TopicArt scene="identity" featured />
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import {morphNavigation,takeMotionReturn} from '@/utils/sharedMotion'
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAuthToken, getCurrentUser, setCurrentUser } from '@/utils/authStorage'
import axios from 'axios'
import CoursePlayer from '@/components/CoursePlayer.vue'
import { normalizeCourses } from '@/utils/courseCatalog'
import { loadCourseCollections, setCourseCollected } from '@/utils/courseCollections'
import { useLearningHistory } from '@/composables/useLearningHistory'

const router = useRouter()
function backFromProfile(){
  const record=takeMotionReturn('profile')
  return morphNavigation(document.querySelector('[data-profile-avatar]'),()=>router.push(record?.path || '/learning-center'),()=>document.querySelector('[data-user-avatar]'),{round:true})
}

const currentUser = ref(getCurrentUser())
const isLogin = computed(() => !!currentUser.value)
const displayName = computed(() => currentUser.value?.name || currentUser.value?.username || '')
const roleText = computed(() => ({student:'学生', teacher:'教师', admin:'管理员'}[currentUser.value?.role] || '学生'))
const roleBadgeClass = computed(() => (String(currentUser.value?.role || '') === 'teacher' ? 'badge-teacher' : 'badge-student'))

const form = ref({
  id: currentUser.value?.id || '',
  name: currentUser.value?.name || '',
  avatar: currentUser.value?.avatar || 'https://picsum.photos/seed/user/100/100'
})

const origin = ref({ ...form.value })
const saving = ref(false)
const profileEditorOpen = ref(false)

const favoriteCourses = ref([])
const loadingCollections = ref(false)
const collectionsError = ref('')
const unavailableCount = ref(0)
const removingCourse = ref('')
const favoritePlayerOpen = ref(false)
const favoritePlaying = ref(null)
const { history: learningHistory, save: saveLearningHistory } = useLearningHistory()
const favoriteResume = computed(() => learningHistory.value.find(item => item.id === favoritePlaying.value?.id) || null)
let collectionRequest = 0
let playbackOwner = null
async function loadCollections() {
  const request = ++collectionRequest
  if (!getCurrentUser()?.id) { favoriteCourses.value = []; loadingCollections.value = false; return }
  loadingCollections.value = true
  collectionsError.value = ''
  try {
    const data = await loadCourseCollections()
    if (!data || request !== collectionRequest) return
    favoriteCourses.value = normalizeCourses(data.courses)
    unavailableCount.value = data.unavailableCount || 0
    currentUser.value = getCurrentUser()
  } catch (error) {
    if (request === collectionRequest) collectionsError.value = error.message || '收藏加载失败，请重试'
  } finally { if (request === collectionRequest) loadingCollections.value = false }
}
const favoriteOrigin = ref(null)
function playFavorite(course, event) {
  favoriteOrigin.value=event?.currentTarget?.closest('.favorite-course')?.querySelector('.favorite-cover') || event?.currentTarget
  playbackOwner = getCurrentUser()?.id
  saveLearningHistory(course.id)
  favoritePlaying.value = course
  favoritePlayerOpen.value = true
}
function saveFavoriteProgress(progress) {
  if (favoritePlaying.value && playbackOwner === getCurrentUser()?.id) saveLearningHistory(favoritePlaying.value.id, progress)
}
async function removeFavorite(course) {
  if (removingCourse.value) return
  removingCourse.value = String(course.id)
  try { await setCourseCollected(course.id, false); ElMessage.success('已取消收藏') }
  catch (error) { ElMessage.error(error.message || '取消收藏失败，请重试') }
  finally { removingCourse.value = '' }
}
function syncCollections() {
  currentUser.value = getCurrentUser()
  const ids = new Set((currentUser.value?.collectedCourses || []).map(String))
  favoriteCourses.value = favoriteCourses.value.filter(course => ids.has(String(course.id)))
  loadCollections()
}

const loadingOverview = ref(false)
const points = ref(0)
const signedToday = ref(false)
const consecutiveDays = ref(0)
const totalSubmissions = ref(0)
const successRate = ref(0)
const passedUnique = ref(0)
const totalWrong = ref(0)
const distinctWrongProblems = ref(0)
const recentHistory = ref([])
const recentExchanges = ref([])

const level = computed(() => Math.max(1, Math.floor((points.value || 0) / 500) + 1))

const goLogin = () => {
  router.push('/login')
}

const reset = () => {
  form.value = { ...origin.value }
}

const openProfileEditor = () => { reset(); profileEditorOpen.value = true }

const randomAvatar = () => {
  const seed = `${form.value.id || 'user'}_${Date.now()}`
  form.value.avatar = `https://picsum.photos/seed/${seed}/100/100`
}

const handleAvatarChange = (uploadFile) => {
  const file = uploadFile?.raw
  if (!file) return
  if (!file.type?.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    form.value.avatar = String(reader.result || '')
  }
  reader.readAsDataURL(file)
}

const formatTime = (value) => {
  if (!value) return ''
  const t = String(value)
  if (t.includes('T')) return t.replace('T', ' ').slice(0, 16)
  if (t.length >= 16) return t.slice(0, 16)
  return t
}

const exchangeStatusText = (status) => {
  const map = { pending: '待发货', completed: '已完成', cancelled: '已取消' }
  return map[status] || String(status || '')
}

const exchangeStatusClass = (status) => {
  const map = { pending: 'warn', completed: 'ok', cancelled: 'muted' }
  return map[status] || 'muted'
}

const loadOverview = async () => {
  if (!isLogin.value) return
  const userId = String(currentUser.value?.id || '')
  if (!userId) return
  loadingOverview.value = true
  try {
    const results = await Promise.allSettled([
      axios.get('/api/points', { params: { user_id: userId } }),
      axios.get('/api/daily-signin/status', { params: { user_id: userId } }),
      axios.get(`/api/analysis/${encodeURIComponent(userId)}`),
      axios.get(`/api/analysis/knowledge/${encodeURIComponent(userId)}`, { params: { limit: 200 } }),
      axios.get('/api/points/records', { params: { user_id: userId } }),
      axios.get(`/api/history/${encodeURIComponent(userId)}`)
    ])

    const pointsRes = results[0].status === 'fulfilled' ? results[0].value?.data : null
    if (pointsRes?.success) points.value = Number(pointsRes.points || 0)

    const signinRes = results[1].status === 'fulfilled' ? results[1].value?.data : null
    if (signinRes?.success) {
      signedToday.value = !!signinRes.signed
      consecutiveDays.value = Number(signinRes.consecutiveDays || 0)
    }

    const analysisRes = results[2].status === 'fulfilled' ? results[2].value?.data : null
    if (analysisRes) {
      totalSubmissions.value = Number(analysisRes.total_submissions || 0)
      successRate.value = Number(analysisRes.success_rate || 0)
      passedUnique.value = Number(analysisRes.passed_unique || 0)
    }

    const knowledgeRes = results[3].status === 'fulfilled' ? results[3].value?.data : null
    if (knowledgeRes?.success) {
      totalWrong.value = Number(knowledgeRes.total_wrong || 0)
      distinctWrongProblems.value = Number(knowledgeRes.distinct_problems || 0)
    }

    const recordsRes = results[4].status === 'fulfilled' ? results[4].value?.data : null
    if (recordsRes?.success && Array.isArray(recordsRes.records)) {
      recentExchanges.value = recordsRes.records.slice(0, 6)
    }

    const historyRes = results[5].status === 'fulfilled' ? results[5].value?.data : null
    if (historyRes && Array.isArray(historyRes.history)) {
      recentHistory.value = historyRes.history.slice(0, 6)
    }
  } finally {
    loadingOverview.value = false
  }
}

const save = async () => {
  if (!isLogin.value) return
  const name = form.value.name?.trim()
  if (!name) {
    ElMessage.warning('昵称不能为空')
    return
  }

  saving.value = true
  try {
    const token = getAuthToken()
    if (!token) {
      ElMessage.error('登录已失效，请重新登录')
      router.push('/login')
      return
    }

    const res = await fetch('/api/users/me', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        name,
        avatar: form.value.avatar
      })
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '保存失败')
    }

    const user = data?.user || {}
    const nextUser = {
      id: user.id,
      role: user.role || currentUser.value?.role,
      name: user.name || user.username || name,
      avatar: user.avatar || form.value.avatar,
      collectedCourses: user.collectedCourses || currentUser.value?.collectedCourses || []
    }

    setCurrentUser(nextUser)
    currentUser.value = nextUser
    form.value.id = nextUser.id
    origin.value = { ...form.value }

    window.dispatchEvent(new Event('user-updated'))
    profileEditorOpen.value = false
    ElMessage.success('保存成功')
    loadOverview()
  } catch (e) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const syncUserFromStorage = () => {
  if (currentUser.value?.id !== getCurrentUser()?.id) {
    favoriteCourses.value = []
    profileEditorOpen.value = false
    favoritePlayerOpen.value = false
    favoritePlaying.value = null
  }
  currentUser.value = getCurrentUser()
  form.value.id = currentUser.value?.id || ''
  form.value.name = currentUser.value?.name || ''
  form.value.avatar = currentUser.value?.avatar || 'https://picsum.photos/seed/user/100/100'
  origin.value = { ...form.value }
  loadOverview()
  loadCollections()
}

onMounted(() => {
  if (isLogin.value) loadOverview()
  if (isLogin.value) loadCollections()
  window.addEventListener('user-updated', syncUserFromStorage)
  window.addEventListener('course-collections-updated', syncCollections)
  window.addEventListener('focus', loadCollections)
})

onBeforeUnmount(() => {
  collectionRequest++
  window.removeEventListener('user-updated', syncUserFromStorage)
  window.removeEventListener('course-collections-updated', syncCollections)
  window.removeEventListener('focus', loadCollections)
})
</script>

<style scoped>
.profile-page { min-height: calc(100vh - 60px); background: #f5f6fb; color: #26364d; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; }
.profile-container { max-width: 1200px; padding: 30px 24px 48px; margin: 0 auto; }
.profile-header { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 22px; }
.profile-header h1 { margin: 0; font-size: 26px; font-weight: 700; letter-spacing: 1px; color: #273751; }
.profile-header p { margin: 9px 0 0; font-size: 13px; color: #8994a8; }
.header-note { display: flex; align-items: center; gap: 7px; color: #9a9cba; font-size: 12px; }
.profile-grid, .content-main, .content-side { display: grid; gap: 20px; min-width: 0; align-content: start; }
.identity-card { display: flex; justify-content: space-between; align-items: center; gap: 22px; background: linear-gradient(105deg, #fff 25%, #f0eefc); border: 1px solid #e5e5f2; padding: 24px 28px; border-radius: 16px; }
.identity-person { display: flex; gap: 18px; align-items: center; min-width: 0; }
.avatar { display: block; width: 68px; height: 68px; object-fit: cover; border-radius: 50%; border: 3px solid #fff; box-shadow: 0 4px 16px #46538016; flex-shrink: 0; }
.avatar-initial { display: grid; place-items: center; background: #8a81df; color: white; font-size: 25px; }
.user-meta { min-width: 0; }.identity-name { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
.user-name { margin: 0; font-size: 22px; font-weight: 650; color: #2b3652; overflow-wrap: anywhere; }
.user-sub { margin: 9px 0 0; color: #9aa3b7; font-size: 11px; overflow-wrap: anywhere; }
.user-sub .mono { margin-left: 7px; font-size: 11px; color: #8993a7; }
.mono { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
.badge, .level-badge { border-radius: 5px; padding: 3px 7px; font-size: 10px; line-height: 1.4; font-weight: 500; }.badge-student { background: #eaf1ff; color: #6488cb; }.badge-teacher { background: #eee8fd; color: #8c69c4; }.level-badge { color: #a58a56; background: #f6f0e3; }
.edit-profile-button { flex-shrink: 0; background: #ffffffb8; border-color: #dcd9ef; color: #776aa9; }.edit-profile-button .el-icon { margin-right: 6px; }
.profile-card { border-radius: 14px; border: 1px solid #e8eaf3; box-shadow: 0 3px 12px #28396303; min-width: 0; background: white; }
.profile-card :deep(.el-card__body) { padding: 22px; }.overview-card :deep(.el-card__body) { padding: 17px 24px 23px; }
.section-heading { display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 20px; }.section-title { display: flex; align-items: center; gap: 8px; margin: 0; color: #35425b; font-size: 15px; font-weight: 650; }.section-caption { font-size: 12px; color: #8a94a9; margin: 7px 0 0; }.section-hint { font-size: 11px; color: #8f9bb0; font-weight: 400; margin-left: 4px; }
.section-heading .el-button { color: #7c88a0; font-size: 12px; height: 26px; padding: 5px 8px; }.section-heading .el-button .el-icon { margin-right: 5px; }
.overview-header { margin-bottom: 12px; }.overview-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 0; }.kpi { padding: 2px 20px 0; border-left: 1px solid #eff0f6; min-width: 0; }.kpi:first-child { border-left: 0; padding-left: 0; }.kpi:last-child { padding-right: 0; }
.kpi-label { display: flex; align-items: center; gap: 7px; font-size: 12px; color: #748198; }.kpi-label .el-icon { font-size: 15px; color: #a298d8; }.kpi:nth-child(2) .el-icon { color: #77b5a6; }.kpi:nth-child(3) .el-icon { color: #7b9ecc; }.kpi:nth-child(4) .el-icon { color: #a493cd; }.kpi:nth-child(5) .el-icon { color: #d4a680; }
.kpi-value { font-size: 27px; font-weight: 650; color: #3b4761; margin-top: 9px; letter-spacing: -.5px; line-height: 1.3; font-variant-numeric: tabular-nums; }.kpi-value small { font-size: 12px; color: #8793a9; margin-left: 5px; font-weight: 400; }.signin-value { font-size: 23px; line-height: 1.53; }.signin-value.signed { color: #6caa94; }.kpi-sub { color: #8f9bb0; font-size: 11px; margin-top: 7px; line-height: 1.5; }
.profile-content { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 20px; align-items: start; }.collections-header { align-items: flex-start; }.collection-count { display: inline-grid; place-items: center; background: #f0eefc; color: #8b7dca; min-width: 20px; height: 19px; padding: 0 5px; border-radius: 5px; font-size: 10px; font-weight: 500; }
.favorites-empty { display: flex; align-items: center; gap: 22px; border-radius: 11px; background: #f8f8fe; padding: 26px 24px; }.empty-collection-icon { width: 62px; height: 62px; display: grid; place-items: center; border-radius: 18px; background: #edeafa; color: #b0a3de; font-size: 30px; flex-shrink: 0; }.favorites-empty h3 { font-size: 14px; font-weight: 500; color: #68738f; margin: 0 0 8px; }.favorites-empty p { color: #8a94a9; font-size: 12px; line-height: 1.8; margin: 0 0 13px; }.favorites-empty .el-button { font-size: 12px; height: 30px; border-radius: 6px; }.favorites-empty .el-icon { margin-left: 4px; }.empty-collection-icon .el-icon { margin: 0; }
.favorite-list { display: grid; gap: 12px; }.favorite-course { display: flex; gap: 16px; min-width: 0; padding: 12px; border: 1px solid #eef0f7; border-radius: 11px; background: #fafbfe; }.favorite-cover { position: relative; width: 152px; aspect-ratio: 16 / 10; flex-shrink: 0; align-self: flex-start; border: 0; border-radius: 7px; padding: 0; overflow: hidden; background: #eceef6; cursor: pointer; }.favorite-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }.favorite-duration { position: absolute; bottom: 5px; right: 5px; border-radius: 4px; padding: 3px 5px; color: #fff; background: #1e263ba6; font-size: 9px; }.favorite-play { display: grid; place-items: center; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 29px; height: 29px; border-radius: 50%; background: #29334d80; color: white; font-size: 23px; }
.favorite-content { flex: 1; min-width: 0; }.favorite-content h3 { margin: 0; font-size: 14px; color: #4b566f; line-height: 1.6; font-weight: 600; overflow-wrap: anywhere; }.favorite-meta { font-size: 11px; color: #7f8ba2; margin: 5px 0; }.favorite-desc { font-size: 11px; line-height: 1.6; color: #8a94a6; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; margin: 5px 0 11px; }.favorite-actions { display: flex; gap: 6px; flex-wrap: wrap; }.favorite-actions .el-button { font-size: 11px; height: 28px; padding: 5px 9px; border-radius: 5px; }.favorite-actions .el-button .el-icon { margin-right: 4px; }.favorite-actions .el-button + .el-button { margin-left: 0; }.favorite-actions .el-button.is-text { color: #8792a6; }
.quick-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }.quick-btn { display: flex; align-items: center; gap: 10px; text-decoration: none; color: #68778f; background: #fafbfe; border: 1px solid #f1f2f8; border-radius: 9px; padding: 12px 10px; font-size: 12px; transition: background .15s, border-color .15s; }.quick-btn:hover { background: #f2f0fd; border-color: #e6e0f7; }.quick-icon { display: grid; place-items: center; width: 27px; height: 27px; border-radius: 7px; font-size: 15px; flex-shrink: 0; }.quick-icon.purple { background: #f0ebfb; color: #a291d6; }.quick-icon.blue { background: #eaf1fc; color: #8da8d4; }.quick-icon.orange { background: #fff1e5; color: #d7ab87; }.quick-icon.green { background: #e9f4ef; color: #8cb9a9; }
.more-link { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; color: #8575aa; text-decoration: none; font-size: 12px; }.more-link:hover { color: #7261bc; }.activity-list { display: grid; }.activity-item { display: grid; grid-template-columns: 80px minmax(0, 1fr) 52px 115px; gap: 14px; align-items: center; padding: 14px 0; border-top: 1px solid #f0f1f6; font-size: 11px; }.activity-item:first-child { border-top: 0; padding-top: 0; }.activity-item:last-child { padding-bottom: 0; }.language-tag { color: #9991c5; border-radius: 5px; background: #f3f0fc; padding: 4px 8px; font-size: 10px; justify-self: start; }.record-title { color: #728098; }.ellipsis { white-space: nowrap; text-overflow: ellipsis; overflow: hidden; min-width: 0; }.muted { color: #8b96aa; font-size: 11px; }.status { display: inline-flex; align-items: center; gap: 5px; font-size: 11px; justify-self: end; white-space: nowrap; }.status i { display: inline-block; width: 4px; height: 4px; border-radius: 50%; background: currentColor; }.status.ok { color: #5f9b83; }.status.bad { color: #c67f85; }.status.warn { color: #ccad7a; }.status.muted { color: #a8b0c1; }.activity-item time { justify-self: end; font-size: 11px; }
.small-empty { padding: 20px 5px 22px; text-align: center; }.small-empty > .el-icon { color: #d4d0e7; background: #f7f6fc; padding: 12px; width: 50px; height: 50px; border-radius: 14px; font-size: 24px; margin-bottom: 12px; }.small-empty p { font-size: 12px; color: #8592a7; margin: 0 0 7px; }.exchange-list { display: grid; gap: 17px; }.exchange-item { display: flex; align-items: center; gap: 11px; }.exchange-icon { display: grid; place-items: center; background: #fbf3e9; color: #d5b695; border-radius: 9px; width: 35px; height: 35px; flex-shrink: 0; }.exchange-info { flex: 1; display: grid; gap: 6px; min-width: 0; font-size: 11px; color: #8c96ab; }.exchange-state { display: grid; gap: 6px; text-align: right; }.points-cost { color: #ac9e83; font-size: 11px; }.exchange-state .status { font-size: 9px; }
.editor-avatar { display: flex; gap: 22px; align-items: center; padding: 6px 0 28px; }.editor-avatar .avatar { width: 82px; height: 82px; }.avatar-actions { display: grid; gap: 9px; }.avatar-actions .el-button + .el-button { margin-left: 0; }.form-section { padding-top: 4px; }.editor-hint { font-size: 12px; line-height: 1.7; }.form-actions { margin-top: 28px; display: flex; justify-content: flex-end; gap: 10px; }.form-actions .el-button + .el-button { margin-left: 0; }.login-card { margin-top: 20px; }.unavailable-note { line-height: 1.7; margin-bottom: 12px; }
.profile-page :deep(.el-button--primary) { --el-color-primary: #8578ce; --el-color-primary-light-3: #a297dd; --el-color-primary-dark-2: #7567bd; }
@media(max-width: 1000px) { .profile-content { grid-template-columns: minmax(0, 1fr) 280px; gap: 16px; }.kpi { padding: 2px 12px 0; }.favorite-cover { width: 125px; }.favorite-desc { display: none; }.favorite-actions { margin-top: 11px; }.quick-btn { flex-direction: column; gap: 8px; }.favorites-empty { padding: 23px 18px; gap: 15px; }.activity-item { grid-template-columns: 65px minmax(0,1fr) 45px 100px; gap: 8px; } }
@media(max-width: 760px) { .profile-container { padding: 23px 16px 32px; }.header-note { display: none; }.profile-header h1 { font-size: 23px; }.profile-content { grid-template-columns: 1fr; }.content-side { grid-template-columns: repeat(2, minmax(0,1fr)); align-items: start; }.overview-grid { grid-template-columns: repeat(3, minmax(0,1fr)); gap: 20px 0; }.kpi:nth-child(4) { border-left: 0; padding-left: 0; }.identity-card { padding: 20px; }.identity-person { gap: 13px; }.user-name { font-size: 19px; }.avatar { width: 57px; height: 57px; }.favorite-cover { width: 152px; }.favorite-desc { display: block; }.quick-btn { flex-direction: row; }.profile-grid, .content-main { gap: 16px; } }
@media(max-width: 520px) { .profile-container { padding: 22px 14px 28px; }.profile-header { margin-bottom: 17px; }.profile-header p { font-size: 12px; }.identity-card { display: grid; grid-template-columns: minmax(0,1fr); padding: 18px 16px; gap: 12px; }.identity-person { flex: 1; }.identity-name { gap: 6px; }.user-name { font-size: 18px; }.avatar { width: 52px; height: 52px; }.user-sub, .user-sub .mono { font-size: 9px; }.edit-profile-button { margin-left: 65px; justify-self: start; font-size: 11px; height: 28px; }.profile-card :deep(.el-card__body) { padding: 18px; }.overview-card :deep(.el-card__body) { padding: 15px 17px 20px; }.overview-grid { grid-template-columns: repeat(2, minmax(0,1fr)); gap: 20px 0; }.kpi { padding: 0 14px; }.kpi:nth-child(odd) { border-left: 0; padding-left: 0; }.kpi:nth-child(even) { border-left: 1px solid #eff0f6; padding-left: 14px; }.kpi:last-child { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr auto; align-items: center; padding-top: 15px; border-top: 1px solid #eff0f6; }.kpi:last-child .kpi-value { grid-column: 2; grid-row: 1 / span 2; margin: 0; }.kpi-value { font-size: 25px; }.signin-value { font-size: 22px; }.section-heading { margin-bottom: 17px; }.section-title { font-size: 14px; }.content-main, .content-side { display: contents; }.collections-card { order: 1; }.quick-card { order: 2; }.activity-card { order: 3; }.exchange-card { order: 4; }.quick-actions { grid-template-columns: repeat(3, minmax(0,1fr)); gap: 9px; }.quick-btn { flex-direction: column; padding: 12px 6px; font-size: 11px; }.favorites-empty { padding: 22px 16px; align-items: flex-start; gap: 14px; }.empty-collection-icon { width: 42px; height: 42px; border-radius: 12px; font-size: 23px; }.favorites-empty h3 { font-size: 12px; }.favorite-course { padding: 10px; gap: 12px; }.favorite-cover { width: 110px; aspect-ratio: 1 / 1; }.favorite-content h3 { font-size: 12px; line-height: 1.5; }.favorite-meta { font-size: 9px; line-height: 1.6; }.favorite-desc { display: none; }.favorite-actions { margin-top: 10px; gap: 0; }.favorite-actions .el-button { font-size: 10px; padding: 5px 8px; height: 28px; }.activity-item { grid-template-columns: 64px minmax(0,1fr) 40px; gap: 8px; padding: 13px 0; }.activity-item time { grid-column: 2 / -1; justify-self: start; font-size: 9px; margin-top: -3px; }.section-hint { font-size: 9px; } }
:global(#app.teacher-mode) .profile-header h1 { color: #f0edff; }
:global(#app.teacher-mode) .profile-header p, :global(#app.teacher-mode) .header-note { color: #aaa3c8; }
</style>

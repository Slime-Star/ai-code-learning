<template>
  <div class="daily-page">
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-left">
          <div class="hero-date"><el-icon><Calendar /></el-icon>每日打卡 · {{ todayText }}</div>
          <h1>每天一小步，编程更进一步</h1>
          <p class="hero-subtitle">签到积累坚持，练习巩固所学。今天，也为自己留一点进步的时间。</p>
          <div class="hero-actions">
            <el-button ref="signinButton" class="signin-button" :class="{'signin-confirmed':!!signinReward}" :loading="signinLoading" :disabled="checkedToday || signinLoading" @click="checkIn">
              <el-icon v-if="checkedToday"><Check /></el-icon>
              {{ checkedToday ? '今日已签到' : '立即签到 · 领积分' }}
            </el-button>
            <button class="hero-link" @click="goToWrongQuestions">打开错题本 <el-icon><ArrowRight /></el-icon></button>
          </div>
          <div class="reward-note">每日签到 10 积分起，连续签到最高每日 40 积分</div>
        </div>
        <div class="today-plan">
          <div class="plan-heading"><span>今日小目标</span><span class="plan-count">{{ dailySteps }} / 2 完成</span></div>
          <div class="plan-progress" role="progressbar" aria-label="今日目标完成进度" :aria-valuenow="dailySteps" aria-valuemin="0" aria-valuemax="2"><span :style="{ width: `${dailySteps * 50}%` }"></span></div>
          <div class="plan-step" :class="{ complete: checkedToday }"><span class="step-mark"><el-icon v-if="checkedToday"><Check /></el-icon><template v-else>1</template></span><span>完成今日签到</span><span class="step-state">{{ checkedToday ? '已完成' : '待签到' }}</span></div>
          <div class="plan-step" :class="{ complete: doneCount > 0 }"><span class="step-mark"><el-icon v-if="doneCount > 0"><Check /></el-icon><template v-else>2</template></span><span>完成一道编程练习</span><span class="step-state">{{ doneCount > 0 ? '已完成' : '待练习' }}</span></div>
          <p class="plan-message" aria-live="polite">{{ dailyGoalMessage }}</p>
        </div>
      </div>
    </section>

    <main class="content">
      <div class="daily-summary" aria-label="今日学习概览">
        <div class="summary-item"><span class="summary-icon streak-icon"><el-icon><Calendar /></el-icon></span><div><span class="summary-label">连续签到</span><strong>{{ streak }} <small>天</small></strong></div></div>
        <div class="summary-item" :class="{'points-received':!!signinReward}"><span ref="pointsTarget" class="summary-icon points-icon"><el-icon><Trophy /></el-icon></span><div><span class="summary-label">我的积分</span><strong><AnimatedNumber :value="points" :animate="!!signinReward" /> <small>积分</small></strong></div></div>
        <div class="summary-item"><span class="summary-icon practice-icon"><el-icon><Check /></el-icon></span><div><span class="summary-label">今日完成练习</span><strong>{{ doneCount }} <small>题</small></strong></div></div>
      </div>

      <section class="next-practice" data-motion-key="daily-recommended" aria-label="下一步练习">
        <div class="next-copy">
          <span class="next-eyebrow">{{ recommendedExercise?.isTeacherTask ? '教师任务优先' : recommendedExercise ? '从这一题开始' : '继续保持学习节奏' }}</span>
          <h2>{{ recommendedExercise?.title || (allExercises.length && doneCount === allExercises.length ? '今天的练习已全部完成' : '试试其他方向的练习') }}</h2>
          <p v-if="recommendedExercise"><span>{{ recommendedExercise.languageLabel }}</span><span>·</span>{{ recommendedExercise.description }}</p>
          <p v-else>{{ doneCount === allExercises.length ? '做得不错！可以回顾错题，把今天学到的内容再巩固一次。' : '当前筛选下没有未完成的题目，可以调整筛选或复习已完成的练习。' }}</p>
        </div>
        <el-button v-if="recommendedExercise" type="primary" class="next-button" @click="startPractice(recommendedExercise, $event)">开始练习 <el-icon><ArrowRight /></el-icon></el-button>
        <el-button v-else plain @click="resetFilters">浏览全部练习</el-button>
      </section>

      <section class="practice-section" aria-labelledby="practice-title">
        <div class="section-heading"><div><h2 id="practice-title">今日练习</h2><p>按语言与知识点挑选，教师任务优先展示</p></div><el-button class="refresh-button" text :icon="Refresh" :loading="refreshing" @click="refreshProgress">刷新进度</el-button></div>
        <div class="practice-toolbar">
          <el-input v-model="searchQuery" placeholder="搜索题目或知识点" :prefix-icon="Search" clearable aria-label="搜索题目或知识点" class="exercise-search" />
          <el-select v-model="selectedLang" placeholder="全部语言" clearable aria-label="练习语言"><el-option label="JavaScript" value="javascript" /><el-option label="Python" value="python" /><el-option label="Java" value="java" /><el-option label="C" value="c" /></el-select>
          <el-select v-model="selectedTopic" placeholder="全部知识点" clearable aria-label="练习知识点"><el-option v-for="topic in topicOptions" :key="topic" :label="topic" :value="topic" /></el-select>
        </div>
        <div class="exercise-scopes" role="group" aria-label="练习完成状态">
          <button v-for="scope in scopeOptions" :key="scope.value" :class="{ active: selectedScope === scope.value }" :aria-pressed="selectedScope === scope.value" @click="selectedScope = scope.value">{{ scope.label }} <span>{{ scope.count }}</span></button>
        </div>
        <div class="filter-summary"><span role="status">共 {{ displayedExercises.length }} 道练习<span v-if="displayedExercises.length">，已完成 {{ visibleDoneCount }} 道</span></span><el-button v-if="hasFilters" link type="primary" @click="resetFilters">清除筛选</el-button></div>
        <el-alert v-if="teacherTasksError" class="task-notice" :title="teacherTasksError" type="warning" :closable="false" show-icon><template #default><el-button link type="primary" :loading="teacherTasksLoading" @click="loadTeacherTasks">重新加载教师任务</el-button></template></el-alert>
        <el-alert v-else-if="teacherTasksLoading && !teacherTasks.length" class="task-notice" title="正在加载教师任务…" type="info" :closable="false" show-icon />

        <div v-if="displayedExercises.length" class="exercise-grid">
          <article v-for="item in paginatedExercises" :key="item.id" class="exercise-card" @pointerenter="warmMotionRoute(router, `/learn/${item.language}`)" @focusin="warmMotionRoute(router, `/learn/${item.language}`)" :data-motion-key="`practice:${item.id}`" :class="{ 'exercise-complete': isDone(item) }">
            <div class="exercise-card-top"><el-tag :type="tagType(item.language)" effect="light">{{ item.languageLabel }}</el-tag><span class="completion-status" :class="{ done: isDone(item) }"><el-icon v-if="isDone(item)"><Check /></el-icon>{{ isDone(item) ? '今日已完成' : '待完成' }}</span></div>
            <div class="exercise-title-row"><h3>{{ item.title }}</h3><span class="difficulty" :class="{ 'teacher-label': item.isTeacherTask }">{{ item.isTeacherTask ? '教师任务' : item.difficulty }}</span></div>
            <p class="exercise-desc">{{ item.description }}</p>
            <div class="exercise-footer"><span class="exercise-topic" :class="{ 'deadline-warning': item.isTeacherTask && item.dueAt }">{{ item.isTeacherTask ? (item.dueAt ? `截止倒计时：${remainingText(item.dueAt)}` : '教师发布 · 不限时') : item.topic }}</span><el-button :type="isDone(item) ? 'success' : 'primary'" :plain="isDone(item)" size="small" @click="startPractice(item, $event)">{{ isDone(item) ? '再练一次' : '开始练习' }}<el-icon><ArrowRight /></el-icon></el-button></div>
          </article>
        </div>
        <el-empty v-else class="exercise-empty" :description="selectedScope === 'done' ? '还没有符合条件的已完成练习，先完成一道题吧' : selectedScope === 'teacher' ? '当前没有符合条件的教师任务' : '没有找到匹配的题目，换个关键词试试' "><el-button plain @click="resetFilters">查看全部练习</el-button></el-empty>
        <div v-if="displayedExercises.length > pageSize" class="exercise-pagination"><el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="displayedExercises.length" :pager-count="5" layout="prev, pager, next" /></div>
      </section>
    </main>
    <TopicArt scene="calendar" featured />
    <ContentBoundary silent><CheckInReward :reward="signinReward" @finished="finishReward" /></ContentBoundary>
  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import {morphNavigation,routeDestination,takeMotionList,warmMotionRoute,afterSharedNavigation} from '@/utils/sharedMotion'
import ContentBoundary from '@/components/ContentBoundary.vue'
import CheckInReward from '@/components/CheckInReward.vue'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import { computed, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAuthToken, getCurrentUser } from '@/utils/authStorage'
import { getStudyDateKey } from '@/utils/studyDate'
import dailyExercises from '@/config/dailyExercises.json'
import { Calendar, Check, ArrowRight, Refresh, Search, Trophy } from '@element-plus/icons-vue'

const router = useRouter()

const userInfo = ref(getCurrentUser())
const userId = computed(() => userInfo.value?.id || 'guest')
const restoredList=takeMotionList('/daily-checkin',userId.value)
const isLogin = computed(() => !!userInfo.value?.id && String(userInfo.value?.id || '') !== 'guest')
const remotePracticeDone = ref(restoredList?.remoteDone || {})
const teacherTasksLoading = ref(false)
const teacherTasksError = ref('')
const refreshing = ref(false)
const localDoneIds = ref(new Set())
const teacherTasksCacheKey = computed(() => `teacherTasksCache_${userId.value}`)

const now = ref(new Date())
const todayKey = computed(() => getStudyDateKey(now.value))
const todayText = computed(() => new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', month: 'long', day: 'numeric', weekday: 'long' }).format(now.value))
let dateTimer = null,stopReturnRefresh

const storageKey = computed(() => `dailyCheckin_${userId.value}`)
const saved = ref({ last: '', streak: 0 })

const signinLoading = ref(false)
const signedToday = ref(false)
const signinStatusAvailable = ref(false)
const signedConsecutiveDays = ref(0)
const points = ref(0)
const signinButton=ref(null),pointsTarget=ref(null),signinReward=ref(null)
let rewardSequence=0,pageActive=true
function finishReward(id){if(signinReward.value?.id===id)signinReward.value=null}
function celebrateSignin(amount){
  if(!pageActive || !Number.isFinite(amount) || amount<=0)return
  const source=(signinButton.value?.$el || signinButton.value)?.getBoundingClientRect()
  const target=pointsTarget.value?.getBoundingClientRect()
  if(!source || !target)return
  const inView=rect=>rect.bottom>0 && rect.top<window.innerHeight && rect.right>0 && rect.left<window.innerWidth
  const clampX=x=>Math.max(24,Math.min(window.innerWidth-24,x))
  const clampY=y=>Math.max(32,Math.min(window.innerHeight-32,y))
  const to=inView(target)?{x:clampX(target.left+target.width/2),y:clampY(target.top+target.height/2)}:{x:clampX(source.right+25),y:clampY(source.top-25)}
  const from=inView(source)?{x:clampX(source.left+source.width/2),y:clampY(source.top+source.height/2)}:{x:clampX(to.x-50),y:clampY(to.y-50)}
  signinReward.value={id:++rewardSequence,amount,from,to}
}
const pointsCacheKey = computed(() => (isLogin.value ? `points_${userId.value}` : 'points_guest'))

const checkedToday = computed(() => signinStatusAvailable.value ? signedToday.value : saved.value.last === todayKey.value)
const streak = computed(() => {
  const yesterday = getStudyDateKey(new Date(now.value.getTime() - 86400000))
  if (!checkedToday.value && saved.value.last !== yesterday) return 0
  return Math.max(0, Number(signedConsecutiveDays.value || saved.value.streak) || 0)
})

// 跳转到错题本
const goToWrongQuestions = () => {
  router.push('/wrong-questions')
}
const loadRemoteState = async () => {
  const token = getAuthToken()
  if (!token) return
  try {
    const res = await fetch('/api/users/me/state', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) return
    const daily = data?.state?.daily_checkin
    if (daily && typeof daily === 'object') {
      saved.value = {
        last: String(daily.last || ''),
        streak: Number(daily.streak || 0)
      }
      localStorage.setItem(storageKey.value, JSON.stringify(saved.value))
    }
    const practice = data?.state?.practice_done
    if (practice && typeof practice === 'object') {
      remotePracticeDone.value = practice
    }
  } catch {}
}

const saveRemoteState = async () => {
  const token = getAuthToken()
  if (!token) return
  try {
    await fetch('/api/users/me/state', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        daily_checkin: {
          last: saved.value.last,
          streak: saved.value.streak
        }
      })
    })
  } catch {}
}

const loadSigninStatus = async () => {
  if (!isLogin.value) return
  try {
    const res = await fetch(
      `/api/daily-signin/status?user_id=${encodeURIComponent(String(userId.value))}&t=${Date.now()}`,
      { cache: 'no-store' }
    )
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) return
    signedToday.value = !!data?.signed
    signinStatusAvailable.value = true
    signedConsecutiveDays.value = Number(data?.consecutiveDays || 0)
    if (signedToday.value) {
      saved.value = { last: todayKey.value, streak: signedConsecutiveDays.value }
      localStorage.setItem(storageKey.value, JSON.stringify(saved.value))
      saveRemoteState()
    }
  } catch {}
}

const loadPoints = async () => {
  if (!isLogin.value) return
  try {
    const res = await fetch(
      `/api/points?user_id=${encodeURIComponent(String(userId.value))}&t=${Date.now()}`,
      { cache: 'no-store' }
    )
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) return
    points.value = Number(data?.points || 0)
    try {
      localStorage.setItem(pointsCacheKey.value, String(points.value))
    } catch {}
  } catch {}
}

const checkIn = async () => {
  if (checkedToday.value || signinLoading.value) return
  if (!isLogin.value) {
    ElMessage.warning('请先登录再签到')
    router.push('/login')
    return
  }
  signinLoading.value = true
  const owner=String(userId.value)
  try {
    const name = String(userInfo.value?.name || userInfo.value?.username || '')
    const url = `/api/daily-signin?user_id=${encodeURIComponent(String(userId.value))}&user_name=${encodeURIComponent(name)}`
    const res = await fetch(url, { method: 'POST' })
    const data = await res.json().catch(() => ({}))
    if(!pageActive || String(userId.value)!==owner)return
    if (!res.ok || data?.success === false) {
      if (data?.alreadySigned) {
        signedToday.value = true
        signinStatusAvailable.value = true
        await Promise.all([loadSigninStatus(), loadPoints()])
        ElMessage.info('今天已经签到过了')
        return
      }
      throw new Error(data?.message || data?.detail || '签到失败')
    }
    signedToday.value = true
    signinStatusAvailable.value = true
    signedConsecutiveDays.value = Number(data?.consecutiveDays || 0)
    saved.value = { last: todayKey.value, streak: signedConsecutiveDays.value }
    localStorage.setItem(storageKey.value, JSON.stringify(saved.value))
    await saveRemoteState()
    const gained = Number(data?.points || 0)
    if(!pageActive || String(userId.value)!==owner)return
    celebrateSignin(gained)
    points.value = Number(points.value || 0) + (Number.isFinite(gained) ? gained : 0)
    await loadPoints()
    ElMessage.success(gained > 0 ? `签到成功 +${gained} 积分` : '签到成功')
  } catch (e) {
    ElMessage.error(e?.message || '签到失败')
  } finally {
    signinLoading.value = false
  }
}

const getDoneKey = (exerciseId) => `dailyPracticeDone_${userId.value}_${todayKey.value}_${String(exerciseId || 'unknown')}`

const isDone = (item) => {
  const id = String(item?.id || 'unknown')
  const localDone = localDoneIds.value.has(id)
  const remoteDone = !!(remotePracticeDone.value?.[todayKey.value]?.[id])
  return localDone || remoteDone
}

const exercises = ref(restoredList?.exercises || dailyExercises)
const loadExerciseCatalog = async () => {
  try {
    const response = await fetch('/api/catalog/exercises', { cache: 'no-store' })
    const data = await response.json()
    if (!response.ok || !Array.isArray(data.items)) throw new Error()
    exercises.value = data.items
  } catch { /* Keep the bundled catalog when the service is unavailable. */ }
}

const teacherTasks = ref(restoredList?.teacherTasks || [])
const selectedLang = ref(restoredList?.lang || '')
const selectedTopic = ref(restoredList?.topic || '')
const searchQuery = ref(typeof router.currentRoute.value.query.q==='string'?router.currentRoute.value.query.q.slice(0,100):restoredList?.query || '')
const selectedScope = ref(restoredList?.scope || 'all')
const currentPage = ref(restoredList?.page || 1)
const pageSize = 9
const allExercises = computed(() => [...teacherTasks.value, ...exercises.value])
const doneCount = computed(() => allExercises.value.filter(isDone).length)
const dailySteps = computed(() => Number(checkedToday.value) + Number(doneCount.value > 0))
const dailyGoalMessage = computed(() => {
  if (dailySteps.value === 2) return '今日目标已达成！还可以复习错题，巩固今天的收获。'
  if (checkedToday.value) return '签到完成啦，再完成一道练习，就达成今日目标。'
  if (doneCount.value > 0) return '练习已完成，记得签到领取今天的积分。'
  return '签到 + 完成一道练习，让今天的学习有个小收获。'
})
const topicOptions = computed(() => [...new Set(exercises.value.map(item => item.topic).filter(Boolean))])
const matchedExercises = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return allExercises.value.filter(item => {
    if (selectedLang.value && item.language !== selectedLang.value) return false
    if (selectedTopic.value && item.topic !== selectedTopic.value) return false
    if (query && ![item.title, item.description, item.topic, item.languageLabel].join(' ').toLowerCase().includes(query)) return false
    return true
  })
})
const scopeOptions = computed(() => [
  { label: '全部', value: 'all', count: matchedExercises.value.length },
  { label: '未完成', value: 'pending', count: matchedExercises.value.filter(item => !isDone(item)).length },
  { label: '已完成', value: 'done', count: matchedExercises.value.filter(isDone).length },
  { label: '教师任务', value: 'teacher', count: matchedExercises.value.filter(item => item.isTeacherTask).length }
])
const displayedExercises = computed(() => matchedExercises.value.filter(item => {
  if (selectedScope.value === 'pending') return !isDone(item)
  if (selectedScope.value === 'done') return isDone(item)
  if (selectedScope.value === 'teacher') return item.isTeacherTask
  return true
}).map((item, index) => ({ item, index })).sort((a, b) => {
  const completed = Number(isDone(a.item)) - Number(isDone(b.item))
  if (completed) return completed
  const teacher = Number(!!b.item.isTeacherTask) - Number(!!a.item.isTeacherTask)
  if (teacher) return teacher
  if (a.item.isTeacherTask && b.item.isTeacherTask) {
    const dueA = Date.parse(a.item.dueAt) || Infinity
    const dueB = Date.parse(b.item.dueAt) || Infinity
    if (dueA !== dueB) return dueA - dueB
  }
  return a.index - b.index
}).map(entry => entry.item))
const recommendedExercise = computed(() => displayedExercises.value.find(item => !isDone(item) && (!item.isTeacherTask || !item.dueAt || !(Date.parse(item.dueAt) <= now.value.getTime()))))
const paginatedExercises = computed(() => displayedExercises.value.slice((currentPage.value - 1) * pageSize, currentPage.value * pageSize))
const visibleDoneCount = computed(() => displayedExercises.value.filter(isDone).length)
const hasFilters = computed(() => !!(searchQuery.value || selectedLang.value || selectedTopic.value || selectedScope.value !== 'all'))
watch([searchQuery, selectedLang, selectedTopic, selectedScope], () => { currentPage.value = 1 })
watch(() => displayedExercises.value.length, length => { currentPage.value = Math.min(currentPage.value, Math.max(1, Math.ceil(length / pageSize))) })
const resetFilters = () => {
  searchQuery.value = ''
  selectedLang.value = ''
  selectedTopic.value = ''
  selectedScope.value = 'all'
  currentPage.value = 1
}

const tagType = (lang) => {
  if (lang === 'javascript') return 'warning'
  if (lang === 'python') return 'success'
  if (lang === 'java') return 'danger'
  if (lang === 'c') return 'info'
  return 'info'
}

const remainingText = (dueAt) => {
  const raw = String(dueAt || '')
  if (!raw) return '不限时'
  const due = new Date(raw)
  if (Number.isNaN(due.getTime())) return '不限时'
  const ms = due.getTime() - now.value.getTime()
  if (ms <= 0) return '已截止'
  const mins = Math.floor(ms / 60000)
  const days = Math.floor(mins / (60 * 24))
  const hours = Math.floor((mins - days * 60 * 24) / 60)
  const m = mins - days * 60 * 24 - hours * 60
  if (days > 0) return `${days}天${hours}小时`
  if (hours > 0) return `${hours}小时${m}分`
  return `${m}分`
}

const loadTeacherTasks = async () => {
  if (teacherTasksLoading.value) return
  const token = getAuthToken()
  if (!token) return
  if (String(userInfo.value?.role || '') !== 'student') return
  teacherTasksLoading.value = true
  teacherTasksError.value = ''
  try {
    const res = await fetch('/api/student/tasks', {
      headers: { Authorization: `Bearer ${token}` }
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) throw new Error('教师任务暂时未能加载，请稍后重试。')
    const tasks = Array.isArray(data?.tasks) ? data.tasks : []
    const mapped = tasks.map(t => ({
      id: `task-${t.id}`,
      taskId: t.id,
      isTeacherTask: true,
      solutionUnlocked: !!t.solutionUnlocked,
      language: t.language,
      languageLabel: t.language === 'python' ? 'Python' : t.language === 'javascript' ? 'JavaScript' : t.language === 'java' ? 'Java' : t.language === 'c' ? 'C' : t.language,
      difficulty: '教师任务',
      title: t.title,
      description: `${t.class_name ? `【${t.class_name}】` : ''}${t.description || ''}`,
      starterCode: t.starterCode || t.starter_code || '',
      expectedOutput: t.expectedOutput || t.expected_output || '',
      solutionCode: t.solutionCode || t.solution_code || '',
      dueAt: t.dueAt || t.due_at || ''
    }))
    teacherTasks.value = mapped
    readLocalState()
    try {
      sessionStorage.setItem(teacherTasksCacheKey.value, JSON.stringify(mapped))
    } catch {}
  } catch {
    teacherTasksError.value = teacherTasks.value.length ? '教师任务更新失败，正在显示最近一次加载的任务。' : '教师任务加载失败，推荐练习仍可使用。'
  }
  finally {
    teacherTasksLoading.value = false
  }
}

const startPractice = (item, event) => {
  sessionStorage.setItem('dailyPractice', JSON.stringify(item))
  const source=event?.currentTarget?.closest('.exercise-card, .next-practice') || event?.currentTarget
  return morphNavigation(source,()=>router.push(`/learn/${item.language}`),routeDestination('.exercise-brief'),{remember:'practice',from:router.currentRoute.value.fullPath,state:{owner:userId.value,lang:selectedLang.value,topic:selectedTopic.value,query:searchQuery.value,scope:selectedScope.value,page:currentPage.value,exercises:exercises.value,teacherTasks:teacherTasks.value,remoteDone:remotePracticeDone.value}})
}

const readLocalState = () => {
  try {
    const data = JSON.parse(localStorage.getItem(storageKey.value) || '{}')
    saved.value = { last: String(data?.last || ''), streak: Math.max(0, Number(data?.streak) || 0) }
  } catch { saved.value = { last: '', streak: 0 } }
  try {
    const cached = Number(localStorage.getItem(pointsCacheKey.value))
    if (Number.isFinite(cached) && cached >= 0) points.value = cached
  } catch {}
  const completed = new Set()
  for (const item of allExercises.value) {
    try { if (localStorage.getItem(getDoneKey(item.id)) === '1') completed.add(String(item.id)) } catch {}
  }
  localDoneIds.value = completed
}
const refreshProgress = async () => {
  if (refreshing.value) return
  const previousDate = todayKey.value
  now.value = new Date()
  if (previousDate !== todayKey.value) {
    signedToday.value = false
    signinStatusAvailable.value = false
  }
  readLocalState()
  refreshing.value = true
  try {
    await Promise.allSettled([loadRemoteState(), loadSigninStatus(), loadPoints(), loadTeacherTasks(), loadExerciseCatalog()])
    readLocalState()
  } finally { refreshing.value = false }
}
const syncUser = () => {
  signinReward.value=null
  userInfo.value = getCurrentUser()
  remotePracticeDone.value = {}
  teacherTasks.value = []
  teacherTasksError.value = ''
  signedToday.value = false
  signinStatusAvailable.value = false
  signedConsecutiveDays.value = 0
  points.value = 0
  readLocalState()
  refreshProgress()
}
const onFocus = () => { refreshProgress() }
const onStorage = () => { readLocalState() }

onMounted(() => {
  try {
    const cached = JSON.parse(sessionStorage.getItem(teacherTasksCacheKey.value) || 'null')
    if (Array.isArray(cached) && !restoredList) teacherTasks.value = cached
  } catch {}
  if(restoredList){readLocalState();stopReturnRefresh=afterSharedNavigation(refreshProgress)}else refreshProgress()
  window.addEventListener('user-updated', syncUser)
  window.addEventListener('focus', onFocus)
  window.addEventListener('storage', onStorage)
  dateTimer = setInterval(() => {
    const next = new Date()
    if (getStudyDateKey(next) !== todayKey.value) refreshProgress()
    else now.value = next
  }, 60000)
})
onBeforeUnmount(() => {
  stopReturnRefresh?.()
  pageActive=false
  signinReward.value=null
  clearInterval(dateTimer)
  window.removeEventListener('user-updated', syncUser)
  window.removeEventListener('focus', onFocus)
  window.removeEventListener('storage', onStorage)
})
</script>

<style scoped>
.daily-page { min-height: calc(100vh - 60px); background: #f5f7fc; color: #25314c; font-family: "Microsoft YaHei", sans-serif; }
.hero { background: linear-gradient(120deg, #637de4 0%, #7652a9 100%); padding: 38px 24px 58px; color: #fff; }
.hero-inner { max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 40px; }
.hero-left { flex: 1; min-width: 0; }
.hero-date { display: inline-flex; align-items: center; gap: 7px; color: #edf0ff; font-size: 13px; margin-bottom: 14px; }
.hero-left h1 { margin: 0; font-size: 32px; line-height: 1.5; letter-spacing: .5px; }
.hero-subtitle { margin: 12px 0 22px; font-size: 14px; color: #eef0ff; line-height: 1.9; max-width: 560px; }
.hero-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 20px; }
.signin-button { --el-button-bg-color: #f4f5ff; --el-button-text-color: #5147a2; --el-button-border-color: #f4f5ff; --el-button-hover-bg-color: #fff; --el-button-hover-border-color: #fff; --el-button-hover-text-color: #443a94; --el-button-disabled-bg-color: rgba(255,255,255,.15); --el-button-disabled-text-color: #fff; --el-button-disabled-border-color: rgba(255,255,255,.3); height: 40px; padding: 0 20px; font-weight: 600; border-radius: 9px; }
.signin-button .el-icon { margin-right: 6px; }
.signin-button.is-disabled { color: #fff; background: rgba(40,33,97,.24); border-color: rgba(255,255,255,.32); }
.hero-link { display: inline-flex; align-items: center; gap: 6px; border: 0; padding: 8px 0; background: transparent; color: #fff; font: inherit; font-size: 13px; cursor: pointer; }
.hero-link:hover { text-decoration: underline; }
.reward-note { color: #e8eaff; font-size: 12px; margin-top: 14px; line-height: 1.7; }
.today-plan { width: 360px; flex-shrink: 0; padding: 23px 25px; border-radius: 18px; border: 1px solid rgba(255,255,255,.24); background: rgba(38,28,92,.18); box-shadow: inset 0 1px 0 rgba(255,255,255,.05); }
.plan-heading { display: flex; align-items: center; justify-content: space-between; font-size: 16px; font-weight: 600; gap: 10px; }
.plan-count { font-size: 12px; color: #edf0ff; font-weight: 400; }
.plan-progress { height: 5px; border-radius: 8px; background: rgba(255,255,255,.19); margin: 16px 0 20px; overflow: hidden; }
.plan-progress span { height: 100%; display: block; background: #b9f3dd; border-radius: inherit; transition: width .25s; }
.plan-step { display: flex; align-items: center; gap: 9px; margin: 14px 0; font-size: 13px; }
.step-mark { display: grid; place-items: center; width: 23px; height: 23px; border: 1px solid rgba(255,255,255,.35); border-radius: 50%; font-size: 11px; flex-shrink: 0; }
.complete .step-mark { color: #173d32; background: #b9f3dd; border-color: #b9f3dd; }
.step-state { margin-left: auto; font-size: 12px; color: #e3e7ff; }
.complete .step-state { color: #c4f8e5; }
.plan-message { margin: 18px 0 0; line-height: 1.8; font-size: 12px; color: #e5e9ff; }
.content { position: relative; max-width: 1248px; margin: -26px auto 0; padding: 0 24px 48px; }
.daily-summary { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 16px; margin-bottom: 24px; }
.summary-item { display: flex; align-items: center; gap: 14px; padding: 21px 24px; border: 1px solid #e7eaf3; border-radius: 14px; background: #fff; box-shadow: 0 4px 15px rgba(37,49,76,.025); }
.summary-icon { display: grid; place-items: center; width: 44px; height: 44px; border-radius: 13px; font-size: 21px; flex-shrink: 0; }
.streak-icon { background: #fff1e6; color: #c77836; }
.points-icon { background: #f0edff; color: #7960c1; }
.practice-icon { background: #e8f7f1; color: #369776; }
.summary-label { display: block; color: #728098; font-size: 12px; margin-bottom: 6px; }
.summary-item strong { font-size: 25px; color: #24324e; font-weight: 600; line-height: 1; }
.summary-item small { font-size: 12px; font-weight: 400; color: #8490a5; margin-left: 4px; }
.next-practice { display: flex; justify-content: space-between; align-items: center; gap: 24px; background: linear-gradient(110deg,#edf1ff,#f2effb); border: 1px solid #e0e4f6; border-radius: 14px; padding: 23px 26px; margin-bottom: 32px; }
.next-copy { min-width: 0; }
.next-eyebrow { color: #6862ab; font-size: 12px; font-weight: 600; }
.next-copy h2 { margin: 7px 0; font-size: 21px; line-height: 1.5; }
.next-copy p { display: flex; flex-wrap: wrap; gap: 6px; color: #63708a; font-size: 13px; line-height: 1.8; margin: 0; }
.next-button { --el-button-bg-color: #6962c5; --el-button-border-color: #6962c5; --el-button-hover-bg-color: #5c54b8; --el-button-hover-border-color: #5c54b8; height: 40px; padding: 0 21px; border-radius: 8px; flex-shrink: 0; }
.next-button .el-icon { margin-left: 8px; }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-bottom: 22px; }
.section-heading h2 { margin: 0; font-size: 22px; }
.section-heading p { margin: 8px 0 0; color: #7c879b; font-size: 13px; line-height: 1.7; }
.refresh-button { --el-button-text-color: #6962ad; flex-shrink: 0; }
.practice-toolbar { display: grid; grid-template-columns: minmax(200px,1fr) 160px 230px; gap: 12px; margin-bottom: 18px; }
.practice-toolbar .el-select { width: 100%; }
.practice-toolbar :deep(.el-input__wrapper), .practice-toolbar :deep(.el-select__wrapper) { min-height: 40px; border-radius: 8px; }
.exercise-scopes { display: flex; align-items: center; gap: 9px; overflow-x: auto; padding: 0 0 3px; }
.exercise-scopes button { display: inline-flex; align-items: center; gap: 8px; flex-shrink: 0; border: 1px solid transparent; border-radius: 8px; padding: 9px 14px; color: #6a768c; background: transparent; font: inherit; font-size: 13px; cursor: pointer; }
.exercise-scopes button span { border-radius: 5px; background: #e9edf4; padding: 1px 5px; font-size: 11px; }
.exercise-scopes button.active { color: #6259b4; border-color: #ddd9f4; background: #eeebfa; font-weight: 600; }
.exercise-scopes button.active span { background: #ded9f4; }
.exercise-scopes button:hover { background: #eeebfa; }
.filter-summary { display: flex; justify-content: space-between; align-items: center; min-height: 42px; color: #8892a4; font-size: 12px; }
.task-notice { margin-bottom: 16px; }
.exercise-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 16px; }
.exercise-card { min-width: 0; display: flex; flex-direction: column; padding: 20px; border-radius: 13px; background: #fff; border: 1px solid #e4e8f1; transition: border-color .18s,box-shadow .18s; }
.exercise-card:hover { border-color: #c9c6e6; box-shadow: 0 6px 18px rgba(54,47,106,.045); }
.exercise-complete { border-color: #cfe6dc; background: #fdfffe; }
.exercise-card-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 17px; }
.exercise-card-top .el-tag { font-size: 11px; border-radius: 5px; }
.completion-status { display: inline-flex; align-items: center; gap: 3px; font-size: 11px; color: #9aa3b1; }
.completion-status.done { color: #358f6d; }
.exercise-title-row { display: flex; align-items: baseline; gap: 9px; flex-wrap: wrap; margin-bottom: 10px; }
.exercise-title-row h3 { margin: 0; font-size: 16px; line-height: 1.6; font-weight: 600; }
.difficulty { color: #939aab; font-size: 11px; white-space: nowrap; }
.teacher-label { color: #a56a45; background: #fff2e9; border-radius: 4px; padding: 1px 5px; }
.exercise-desc { margin: 0 0 22px; color: #758198; font-size: 13px; line-height: 1.8; flex: 1; overflow-wrap: anywhere; }
.exercise-footer { display: flex; justify-content: space-between; align-items: center; gap: 10px; border-top: 1px solid #f0f2f7; padding-top: 15px; }
.exercise-topic { color: #8a95a8; font-size: 11px; overflow-wrap: anywhere; }
.deadline-warning { color: #ac734d; }
.exercise-footer .el-button { border-radius: 6px; flex-shrink: 0; }
.exercise-footer .el-icon { margin-left: 5px; }
.exercise-empty { background: #fff; border: 1px dashed #dfe4ee; border-radius: 14px; }
.exercise-pagination { display: flex; justify-content: center; padding: 28px 0 0; }
@media (max-width: 1024px) {
  .hero-inner { gap: 24px; }
  .hero-left h1 { font-size: 28px; }
  .today-plan { width: 310px; padding: 22px; }
  .exercise-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
}
@media (max-width: 760px) {
  .hero-inner { flex-direction: column; align-items: stretch; }
  .today-plan { width: 100%; }
  .hero { padding: 28px 20px 52px; }
  .hero-left h1 { font-size: 27px; }
  .hero-subtitle { margin-bottom: 18px; }
  .content { padding: 0 20px 32px; }
  .daily-summary { gap: 10px; margin-bottom: 18px; }
  .summary-item { padding: 17px 13px; gap: 8px; }
  .summary-icon { display: none; }
  .summary-item strong { font-size: 22px; }
  .summary-item small { margin-left: 0; }
  .summary-label { font-size: 11px; }
  .next-practice { padding: 20px; margin-bottom: 26px; align-items: stretch; flex-direction: column; gap: 16px; }
  .next-copy h2 { font-size: 20px; }
  .practice-toolbar { grid-template-columns: minmax(0,1fr) minmax(0,1fr); gap: 10px; }
  .exercise-search { grid-column: 1 / -1; }
  .section-heading { align-items: flex-start; gap: 4px; }
  .section-heading h2 { font-size: 21px; }
  .section-heading p { font-size: 12px; }
  .refresh-button { padding: 6px; }
  .exercise-scopes { gap: 4px; }
  .exercise-scopes button { padding: 8px 10px; gap: 6px; }
  .exercise-grid { grid-template-columns: 1fr; }
}
.points-received .points-icon { animation: signin-points-arrive 900ms ease-out 550ms; }
.signin-button.signin-confirmed { animation: signin-confirm 650ms ease-out; }
.points-received strong { color: #8060aa; transition: color 300ms; }
@keyframes signin-points-arrive { 35% { transform: scale(1.12); box-shadow: 0 0 0 7px #c6a8e32b; } }
@keyframes signin-confirm { 40% { transform: scale(1.04); box-shadow: 0 0 0 7px #eee4ff22; } }
</style>

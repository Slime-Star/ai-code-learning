<template>
  <div class="wrong-page">
    <div class="hero">
      <div class="hero-inner">
        <div class="hero-left">
          <h1>错题本</h1>
          <p>整理你的错误，专项练习，快速进步</p>
          <div class="hero-meta">
            <span class="meta-item">
              <el-icon><Document /></el-icon>
              累计 {{ wrongQuestions.length }} 道错题
            </span>
          </div>
          <div class="hero-actions">
            <el-button type="primary" :loading="loading" @click="refreshWrongQuestions">
              刷新错题
            </el-button>
            <el-button plain @click="$router.push('/daily-checkin')">
              返回每日打卡
            </el-button>
          </div>
        </div>
        <div class="hero-right">
          <TopicArt scene="debug" inverse compact />
          <div class="review-loop"><span>发现错误</span><i>→</i><span>修改验证</span><i>→</i><span>巩固知识</span></div>
        </div>
      </div>
    </div>

    <div class="content">
      <div class="review-summary"><div><small>待复习题目</small><strong>{{ wrongQuestions.length }}<span>道</span></strong></div><div><small>累计记录错误</small><strong>{{ totalErrors }}<span>次</span></strong></div><div><small>涉及编程语言</small><strong>{{ languageCount }}<span>种</span></strong></div><el-button type="primary" :disabled="loading || !displayedWrongQuestions.length" @click="startPractice(displayedWrongQuestions[0], $event)">开始专项复习 ↗</el-button></div>
      <div class="section-title">
        <h2>错题列表</h2>
        <p>按语言/知识点筛选，专项突破</p>
      </div>

      <div class="filters"><el-input v-model="searchQuery" placeholder="搜索题目或知识点" clearable aria-label="搜索错题" class="wrong-search" />
        <el-select v-model="selectedLang" placeholder="选择语言" clearable aria-label="错题语言" style="width: 160px">
          <el-option label="JavaScript" value="javascript" />
          <el-option label="Python" value="python" />
          <el-option label="Java" value="java" />
          <el-option label="C" value="c" />
        </el-select>
        <el-select v-model="selectedTopic" placeholder="选择知识点" clearable aria-label="错题知识点" style="width: 220px">
          <el-option v-for="t in topicOptions" :key="t" :label="t" :value="t" />
        </el-select>
        <el-button plain @click="resetFilters">重置</el-button>
      </div>

      <el-alert v-if="loadError" :title="loadError" type="error" :closable="false" show-icon class="load-error">
        <template #default><el-button v-if="needsLogin" link type="primary" @click="relogin">重新登录</el-button><el-button v-else link type="primary" @click="refreshWrongQuestions">重试加载</el-button></template>
      </el-alert>
      <div v-if="loading && !wrongQuestions.length" class="loading-wrap">
        <el-skeleton :rows="4" animated />
      </div>

      <div v-else-if="!loadError && displayedWrongQuestions.length === 0" class="empty-wrap">
        <el-empty :description="wrongQuestions.length ? '没有符合当前筛选条件的错题' : '暂无错题，练习中的运行错误和提交后不符合预期的答案会记录在这里'">
          <el-button v-if="wrongQuestions.length" plain @click="resetFilters">清除筛选</el-button>
          <el-button v-else type="primary" @click="$router.push('/daily-checkin')">去练习</el-button>
        </el-empty>
      </div>

      <TransitionGroup v-else name="wrong-card" tag="div" class="exercise-grid">
        <el-card
          v-for="item in displayedWrongQuestions"
          :key="`${item.problem_id}-${item.language}`"
          shadow="hover"
          class="exercise-card" @pointerenter="warmMotionRoute(router, `/learn/${item.language}`)" @focusin="warmMotionRoute(router, `/learn/${item.language}`)" :data-motion-key="`wrong:${item.problem_id}:${item.language}`"
        >
          <div class="exercise-head">
            <div class="exercise-lang">
              <el-tag :type="tagType(item.language)" effect="dark">{{ item.languageLabel }}</el-tag>
              <el-tag type="danger" class="difficulty">错题</el-tag>
              <el-tag type="warning" effect="dark">{{ item.errorCount }} 次错误</el-tag>
            </div>
          </div>
          <div class="exercise-body">
            <div class="exercise-title">{{ item.title }}</div>
            <div class="exercise-desc">{{ item.description }}</div>
            <div class="exercise-tags">
              <el-tag v-for="t in (item.topics || []).slice(0, 3)" :key="t" size="small" type="info">{{ t }}</el-tag>
            </div>
            <details v-if="item.latestError" class="last-error"><summary>查看上次报错</summary><pre>{{ item.latestError }}</pre><button class="copy-error" @click="copyError(item.latestError)">复制报错信息</button></details>
          </div>
          <div class="exercise-foot">
            <div class="exercise-meta">
              <span class="meta-item">最近错误: {{ formatTime(item.latestErrorAt) }}</span>
            </div>
            <el-button type="primary" size="small" @click="startPractice(item, $event)">继续修改</el-button>
          </div>
        </el-card>
      </TransitionGroup>
    </div>


  </div>
</template>

<script setup>
import TopicArt from '@/components/TopicArt.vue'
import {morphNavigation,routeDestination,takeMotionList,warmMotionRoute,afterSharedNavigation} from '@/utils/sharedMotion'
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import { getAuthToken as getToken, getCurrentUser, removeAuthToken, removeCurrentUser } from '@/utils/authStorage'
import dailyExercises from '@/config/dailyExercises.json'

const router = useRouter()

const restoredList=takeMotionList('/wrong-questions',getCurrentUser()?.id || 'guest')
const loading = ref(!restoredList?.questions?.length)
const wrongQuestions = ref(restoredList?.questions || [])
const searchQuery=ref(restoredList?.query || '')
const totalErrors=computed(()=>wrongQuestions.value.reduce((sum,item)=>sum+Math.max(0,Number(item.errorCount)||0),0))
const languageCount=computed(()=>new Set(wrongQuestions.value.map(item=>item.language)).size)
async function copyError(text){try{await navigator.clipboard.writeText(text);ElMessage.success('已复制报错信息')}catch{ElMessage.warning('复制失败，请手动选择报错文字')}}
const selectedLang = ref(restoredList?.lang || '')
const selectedTopic = ref(restoredList?.topic || '')
const loadError = ref('')
const needsLogin = ref(false)

const defaultTopics = [
  '语法与标点', '变量/作用域/未定义', '类型与转换',
  '空值/空指针', '数组/下标与越界', '输入输出与解析',
  '递归/栈溢出', '超时/死循环/复杂度'
]
const topicOptions = computed(() => {
  const topics = new Set(defaultTopics)
  wrongQuestions.value.forEach(q => {
    (q.topics || []).forEach(t => topics.add(t))
  })
  return Array.from(topics).sort()
})

const displayedWrongQuestions = computed(() => {
  let list = [...wrongQuestions.value]
  const query=searchQuery.value.trim().toLowerCase()
  if(query)list=list.filter(item=>[item.title,item.description,...(item.topics||[])].join(' ').toLowerCase().includes(query))
  if (selectedLang.value) {
    list = list.filter(q => q.language === selectedLang.value)
  }
  if (selectedTopic.value) {
    list = list.filter(q => (q.topics || []).includes(selectedTopic.value))
  }
  return list.sort((a, b) => b.errorCount - a.errorCount)
})

const tagType = (lang) => {
  const map = {
    javascript: 'success',
    python: 'warning',
    java: 'info',
    c: 'danger'
  }
  return map[lang] || 'info'
}

const formatTime = (t) => {
  if (!t) return '-'
  // SQLite CURRENT_TIMESTAMP is UTC, but does not include a timezone suffix.
  const normalized = String(t).trim().replace(' ', 'T')
  const d = new Date(/(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized) ? normalized : `${normalized}Z`)
  if (Number.isNaN(d.getTime())) return '-'
  return d.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadWrongQuestions = async () => {
  loading.value = !wrongQuestions.value.length
  loadError.value = ''
  needsLogin.value = false
  try {
    const token = getToken()
    if (!token) {
      needsLogin.value = true
      throw new Error('请先登录后查看自己的错题本')
    }
    const res = await fetch('/api/student/wrong-questions', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data.success === false) {
      needsLogin.value = res.status === 401
      throw new Error(needsLogin.value ? '登录已过期，请重新登录后查看错题本' : (data.detail || data.message || '错题加载失败，请重试'))
    }
    wrongQuestions.value = (Array.isArray(data.wrong_questions) ? data.wrong_questions : []).map(item => {
      const original = dailyExercises.find(exercise => exercise.id === item.problem_id && exercise.language === item.language)
      return original && !item.hasQuestionMetadata ? {
        ...item,
        title: original.title,
        description: original.description,
        expectedOutput: original.expectedOutput,
        starterCode: original.starterCode,
        solutionCode: original.solutionCode,
        topics: [...new Set([original.topic, ...(item.topics || [])].filter(Boolean))]
      } : item
    })
  } catch (e) {
    loadError.value = e.message || '错题加载失败，请重试'
  } finally {
    loading.value = false
  }
}

const refreshWrongQuestions = () => loadWrongQuestions()
const relogin = () => {
  removeAuthToken()
  removeCurrentUser()
  window.dispatchEvent(new Event('user-updated'))
  router.push('/login')
}

const resetFilters = () => {
  searchQuery.value=''
  selectedLang.value = ''
  selectedTopic.value = ''
}

const startPractice = (item, event) => {
  const exercise = {
    id: item.problem_id,
    language: item.language,
    languageLabel: item.languageLabel || item.language,
    title: item.title,
    description: item.description,
    difficulty: '中等',
    topics: item.topics || [],
    starterCode: item.lastCode || item.starterCode || '',
    expectedOutput: item.expectedOutput || '',
    solutionCode: item.solutionCode || '',
    isTeacherTask: !!item.isTeacherTask,
    taskId: item.taskId || '',
    solutionUnlocked: !!item.solutionUnlocked,
    fromWrongQuestions: true
  }
  try {
    sessionStorage.setItem('dailyPractice', JSON.stringify(exercise))
    const source=event?.currentTarget?.closest('.exercise-card') || event?.currentTarget
    return morphNavigation(source,()=>router.push(`/learn/${item.language}`),routeDestination('.exercise-brief'),{remember:'practice',from:router.currentRoute.value.fullPath,state:{owner:getCurrentUser()?.id || 'guest',query:searchQuery.value,lang:selectedLang.value,topic:selectedTopic.value,questions:wrongQuestions.value}})
  } catch {
    ElMessage.error('无法打开练习，请允许浏览器保存当前会话后重试')
  }
}

let stopReturnRefresh
onMounted(() => {
  if(restoredList)stopReturnRefresh=afterSharedNavigation(loadWrongQuestions)
  else loadWrongQuestions()
})
onBeforeUnmount(()=>stopReturnRefresh?.())
</script>

<style scoped>
.wrong-page {
  min-height: 100vh;
  background: #f7fafc;
  color: #1a202c;
}
.hero {
  padding: 40px 20px;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f5ff 100%);
}
.hero-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  gap: 40px;
  align-items: center;
}
.hero-left h1 {
  font-size: 40px;
  margin: 0 0 10px;
  color: #096dd9;
}
.hero-left p {
  color: #5c6b7d;
  margin: 0 0 20px;
}
.hero-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #4a5568;
  font-size: 14px;
}
.hero-actions {
  display: flex;
  gap: 12px;
}
.hero-right {
  flex-shrink: 0;
}
.hero-card {
  padding: 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(59,130,246,0.1), rgba(99,102,241,0.12));
  border: 1px solid rgba(59,130,246,0.2);
  min-width: 260px;
}
.hero-card-title {
  font-weight: 700;
  font-size: 18px;
  margin-bottom: 6px;
  color: #1890ff;
}
.hero-card-desc {
  color: #6b7280;
  font-size: 13px;
}
.content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 20px 60px;
}
.section-title {
  margin-bottom: 20px;
}
.section-title h2 {
  font-size: 26px;
  margin: 0 0 6px;
  color: #1e293b;
}
.section-title p {
  color: #6b7280;
  margin: 0;
}
.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.loading-wrap,
.empty-wrap {
  padding: 60px 0;
}
.exercise-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}
.exercise-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
}
.exercise-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.08);
}
.exercise-head {
  padding: 14px 16px 0;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}
.exercise-lang {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.exercise-body {
  padding: 14px 16px;
}
.exercise-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 6px;
  color: #1e293b;
}
.exercise-desc {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.exercise-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.exercise-foot {
  padding: 10px 16px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #e2e8f0;
}
.exercise-meta {
  color: #9ca3af;
  font-size: 12px;
}
.load-error { margin-bottom: 20px; }
.last-error { margin-top: 14px; color: #7c5260; font-size: 12px; }
.last-error summary { cursor: pointer; }
.last-error pre { margin: 10px 0 0; padding: 10px; background: #fff5f5; border-radius: 6px; max-height: 180px; overflow: auto; white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 640px) {
  .hero-inner { flex-direction: column; align-items: stretch; gap: 20px; }
  .hero-left h1 { font-size: 30px; }
  .hero-card { min-width: 0; }
  .filters { flex-wrap: wrap; }
  .filters .el-select { width: 100% !important; }
  .exercise-grid { grid-template-columns: minmax(0, 1fr); }
  .exercise-foot { flex-wrap: wrap; gap: 10px; }
}
.hero{background:linear-gradient(125deg,#677ce4,#7953a7);color:#fff;overflow:hidden}.hero-left h1{color:#fff}.hero-left p,.hero-meta .meta-item{color:#eae1fb}.hero-inner{justify-content:space-between}.hero-right{width:330px;max-width:100%;flex-shrink:0}.hero-right :deep(.topic-art){max-width:100%;margin:0;height:155px}.review-loop{display:flex;justify-content:center;align-items:center;gap:12px;font-size:10px;color:#e7d8f5}.review-loop i{font-style:normal;color:#d1b8eb;animation:review-arrow 2.4s ease-in-out infinite}.review-loop i:last-of-type{animation-delay:.4s}.review-summary{display:flex;align-items:center;gap:28px;flex-wrap:wrap;padding:23px 26px;background:#fff;border:1px solid #e7deef;border-radius:16px;margin-bottom:28px;box-shadow:0 7px 24px #8d70a30a}.review-summary>div{flex:1;min-width:110px}.review-summary small{display:block;font-size:11px;color:#a293af;margin-bottom:9px}.review-summary strong{font:500 28px Consolas,monospace;color:#87649e}.review-summary strong span{font:inherit;font-size:11px;margin-left:8px;color:#b1a1bc}.wrong-search{max-width:300px;min-width:170px}.exercise-card{border-color:#e6ddec;border-radius:15px}.exercise-card:hover{box-shadow:0 12px 28px #9168ad19;transform:translateY(-4px)}.exercise-title{color:#645074}.exercise-tags .el-tag{border-radius:6px}.copy-error{border:0;background:none;color:#9672ae;padding:6px 0;font-size:11px;cursor:pointer}.last-error pre{background:#f6f0fa;color:#8b657c;border:1px solid #e9ddee}.wrong-card-enter-active,.wrong-card-leave-active,.wrong-card-move{transition:opacity 240ms,transform 280ms}.wrong-card-enter-from,.wrong-card-leave-to{opacity:0;transform:translateY(18px)}.wrong-card-leave-active{position:absolute;pointer-events:none}.exercise-grid{position:relative;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr))}@keyframes review-arrow{50%{translate:4px 0;opacity:.5}}@media(max-width:700px){.hero-inner{flex-direction:column;align-items:stretch}.hero-right{align-self:center}.review-summary{gap:20px;padding:20px}.review-summary>.el-button{width:100%}.filters{flex-wrap:wrap}.wrong-search{max-width:none;width:100%}.review-summary strong{font-size:24px}}
</style>

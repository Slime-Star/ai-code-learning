<template>
  <div class="page test-play-page">
    <div class="topbar">
      <el-button @click="goBack">返回测试列表</el-button>
      <div class="title">
        <div class="name">{{ competition?.name || '比赛' }}</div>
        <div class="meta" v-if="competition">
          <el-tag :type="statusTagType" size="small">{{ statusText }}</el-tag>
          <el-tag type="info" size="small">{{ modeText }}</el-tag>
          <span class="meta-item" v-if="competition.duration">时长：{{ competition.duration }}</span>
          <span class="meta-item" v-if="competition.problemCount != null">题目数：{{ competition.problemCount }}</span>
        </div>
      </div>
    </div>

    <div class="content">
      <div v-if="loading" class="loading">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <div v-else-if="errorMessage" class="error">
        <el-empty :description="errorMessage">
          <el-button v-if="showRegisterAction" type="primary" @click="registerAndReload">立即报名</el-button>
          <el-button v-else type="primary" @click="goBack">返回</el-button>
        </el-empty>
      </div>

      <div v-else>
        <div class="info-layout" v-if="competition">
          <div class="info-main">
            <el-card class="info-card" shadow="never">
              <template #header>
                <div class="card-title">测试简介</div>
              </template>
              <div class="desc">{{ competition.detailDesc || competition.desc || '暂无简介' }}</div>
            </el-card>

            <el-card class="info-card" shadow="never">
              <template #header>
                <div class="card-title">时间安排</div>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="报名时间">
                  {{ competition.registerTime || '未设置' }}
                </el-descriptions-item>
                <el-descriptions-item label="比赛时间">
                  {{ competition.competitionTime || '未设置' }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <el-card v-if="rulesList.length" class="info-card" shadow="never">
              <template #header>
                <div class="card-title">测试规则</div>
              </template>
              <ul class="list">
                <li v-for="(r, idx) in rulesList" :key="idx">{{ r }}</li>
              </ul>
            </el-card>

            <el-card v-if="rewardsList.length" class="info-card" shadow="never">
              <template #header>
                <div class="card-title">奖项设置</div>
              </template>
              <ul class="list">
                <li v-for="(r, idx) in rewardsList" :key="idx">{{ r }}</li>
              </ul>
            </el-card>

            <el-card v-if="competition.mode === 'problem_set'" class="info-card" shadow="never">
              <template #header>
                <div class="card-title">题目列表</div>
              </template>
              <el-alert
                v-if="!problems.length"
                type="warning"
                show-icon
                title="该测试尚未配置题目"
              />

              <div v-for="group in groupedProblems" :key="group.key" class="group">
                <div class="group-title">
                  <span class="group-name">{{ group.name }}</span>
                  <span class="group-count">({{ group.items.length }}题)</span>
                </div>
                <el-table :data="group.items" border style="width: 100%">
                  <el-table-column prop="title" label="题目" min-width="240" />
                  <el-table-column prop="language" label="语言" width="120" />
                  <el-table-column prop="points" label="分值" width="90" />
                  <el-table-column label="状态" width="110">
                    <template #default="{ row }">
                      <el-tag v-if="isSubmitted(row)" type="success" size="small">已提交</el-tag>
                      <el-tag v-else type="info" size="small">未提交</el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="120">
                    <template #default="{ row }">
                      <el-button type="primary" size="small" @click="startProblem(row, $event)">开始</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-card>

            <el-card v-else class="info-card" shadow="never">
              <template #header>
                <div class="card-title">参赛说明</div>
              </template>
              <el-alert
                type="info"
                show-icon
                title="该测试为普通测试"
                description="当前页面主要展示测试信息。若需要做题入口，请将测试模式设置为“做题型测试”并配置题目。"
              />
            </el-card>
          </div>

          <div class="info-side">
            <el-card class="info-card" shadow="never">
              <template #header>
                <div class="card-title">测试信息</div>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="状态">{{ statusText }}</el-descriptions-item>
                <el-descriptions-item label="类型">{{ typeText }}</el-descriptions-item>
                <el-descriptions-item label="模式">{{ modeText }}</el-descriptions-item>
                <el-descriptions-item label="难度">{{ competition.difficulty || '未设置' }}</el-descriptions-item>
                <el-descriptions-item label="报名人数">{{ competition.participants ?? 0 }}</el-descriptions-item>
                <el-descriptions-item label="时长">{{ competition.duration || '未设置' }}</el-descriptions-item>
                <el-descriptions-item label="题目数">{{ competition.problemCount ?? 0 }}</el-descriptions-item>
                <el-descriptions-item v-if="competition.status === 'ended'" label="我的得分">
                  <span v-if="myResult"><AnimatedNumber v-if="Number.isInteger(Number(myResult.score)) && Number(myResult.score)>=0" :value="Number(myResult.score)" animate /><span v-else>{{ myResult.score }}</span> / {{ myResult.maxScore }}</span>
                  <span v-else>—</span>
                </el-descriptions-item>
                <el-descriptions-item v-if="competition.status === 'ended'" label="我的名次">
                  <span v-if="myResult">{{ myResult.rank }} / {{ myResult.totalParticipants }}</span>
                  <span v-else>—</span>
                </el-descriptions-item>
              </el-descriptions>

              <div v-if="tagsList.length" class="tags">
                <el-tag v-for="t in tagsList" :key="t" size="small" class="tag">{{ t }}</el-tag>
              </div>
              <div v-if="competition.status === 'ended'" style="margin-top: 12px">
                <el-button size="small" plain :loading="myResultLoading" :disabled="myResultLoading" @click="loadMyResult">刷新成绩</el-button>
              </div>
            </el-card>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {morphNavigation,takeMotionReturn,findMotionElement,routeDestination,takeMotionPage} from '@/utils/sharedMotion'
import AnimatedNumber from '@/components/AnimatedNumber.vue'
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getCurrentUser } from '@/utils/authStorage'

const route = useRoute()
const router = useRouter()

const competitionId = computed(() => String(route.params.id || '').trim())

const loading = ref(true)
const competition = ref(takeMotionPage(route.path,getCurrentUser()?.id || 'guest'))
const problems = ref([])
const mySubmissions = ref(new Map())
const myResultLoading = ref(false)
const myResult = ref(null)
const errorMessage = ref('')
const showRegisterAction = ref(false)

const statusText = computed(() => {
  const s = competition.value?.status
  const map = { registering: '报名中', ongoing: '进行中', ended: '已结束' }
  return map[s] || (s || '')
})

const statusTagType = computed(() => {
  const s = competition.value?.status
  const map = { registering: 'success', ongoing: 'warning', ended: 'info' }
  return map[s] || 'info'
})

const modeText = computed(() => {
  const m = competition.value?.mode
  return m === 'problem_set' ? '做题型测试' : '普通测试'
})

const typeText = computed(() => {
  const t = competition.value?.type
  const map = {
    algorithm: '算法测试',
    web: 'Web开发',
    data: '数据科学',
    ai: '人工智能',
    mobile: '移动开发',
    game: '游戏开发'
  }
  return map[t] || (t || '未设置')
})

const tagsList = computed(() => {
  const raw = competition.value?.tags
  if (Array.isArray(raw)) return raw.map((x) => String(x || '').trim()).filter(Boolean)
  if (typeof raw === 'string') return raw.split(',').map((x) => x.trim()).filter(Boolean)
  return []
})

const rulesList = computed(() => {
  const raw = competition.value?.rules
  if (Array.isArray(raw)) return raw.map((x) => String(x || '').trim()).filter(Boolean)
  if (typeof raw === 'string') return raw.split(',').map((x) => x.trim()).filter(Boolean)
  return []
})

const rewardsList = computed(() => {
  const raw = competition.value?.rewards
  if (Array.isArray(raw)) return raw.map((x) => String(x || '').trim()).filter(Boolean)
  if (typeof raw === 'string') return raw.split(',').map((x) => x.trim()).filter(Boolean)
  return []
})

const groupedProblems = computed(() => {
  const list = problems.value || []
  const buckets = new Map()
  for (const p of list) {
    const key = String(p.category || '').trim() || '未分类'
    if (!buckets.has(key)) buckets.set(key, [])
    buckets.get(key).push(p)
  }
  const groups = []
  for (const [key, items] of buckets.entries()) {
    const sorted = [...items].sort((a, b) => (Number(a.sort || 0) - Number(b.sort || 0)))
    groups.push({ key, name: key, items: sorted })
  }
  return groups
})

const isSubmitted = (p) => {
  const tid = String(p?.taskId || '').trim()
  if (!tid) return false
  if (mySubmissions.value instanceof Map && mySubmissions.value.has(tid)) return true
  const user = getCurrentUser()
  const uid = String(user?.id || 'guest')
  const cid = String(competitionId.value || '')
  try {
    return localStorage.getItem(`competitionSubmitted_${uid}_${cid}_${tid}`) === '1'
  } catch {
    return false
  }
}

const loadMySubmissions = async () => {
  const cid = Number(competitionId.value || 0)
  if (!cid) return
  try {
    const res = await request.get(`/api/competitions/${cid}/my-submissions`)
    const list = res.submissions || []
    const m = new Map()
    for (const it of list) {
      const tid = String(it?.taskId || '').trim()
      if (tid) m.set(tid, it)
    }
    mySubmissions.value = m
  } catch {
    mySubmissions.value = new Map()
  }
}

const loadMyResult = async () => {
  const cid = Number(competitionId.value || 0)
  if (!cid) return
  if (myResultLoading.value) return
  myResultLoading.value = true
  try {
    const res = await request.get(`/api/competitions/${cid}/my-result`)
    myResult.value = res.result || null
  } catch {
    myResult.value = null
  } finally {
    myResultLoading.value = false
  }
}

const goBack = () => {
  const record=takeMotionReturn('test')
  return morphNavigation(document.querySelector('.topbar .title'),()=>router.push('/competition'),()=>findMotionElement(record?.key),{returning:true,afterNavigate:()=>{if(record)window.scrollTo({top:record.scroll,behavior:'instant'})}})
}

const loadCompetition = async () => {
  const cid = Number(competitionId.value || 0)
  if (!cid) throw new Error('测试ID不合法')
  try {
    const res = await request.get(`/api/competitions/${cid}`)
    competition.value = res.data
    return
  } catch (e) {
    if (e?.response?.status !== 404) throw e
  }
  const listRes = await request.get('/api/competitions')
  const list = Array.isArray(listRes?.data) ? listRes.data : []
  const found = list.find((c) => Number(c?.id) === cid) || null
  if (!found) throw new Error('测试不存在')
  competition.value = {
    ...found,
    mode: found?.mode || 'general'
  }
}

const loadProblems = async () => {
  const cid = Number(competitionId.value || 0)
  if (!cid) throw new Error('测试ID不合法')
  try {
    const res = await request.get(`/api/competitions/${cid}/problems`)
    problems.value = res.problems || []
  } catch (e) {
    if (e?.response?.status === 404) {
      problems.value = []
      ElMessage.warning('后端未启用测试题目接口，请重启后端服务后再试')
      return
    }
    if (e?.response?.status === 403) {
      const msg = e?.response?.data?.detail || e?.response?.data?.message
      if (msg) throw new Error(String(msg))
    }
    throw e
  }
}

const registerAndReload = async () => {
  const user = getCurrentUser()
  if (!user?.id) {
    ElMessage.warning('请先登录后再报名')
    router.push('/login')
    return
  }
  const cid = Number(competitionId.value || 0)
  await request.post('/api/competitions/register', {
    competitionId: cid,
    userId: user.id,
    userName: user.name,
    competition_id: cid,
    user_id: user.id,
    user_name: user.name
  })
  ElMessage.success('报名成功')
  await init()
}

const startProblem = (p, event) => {
  const lang = String(p.language || '').trim()
  if (!lang) {
    ElMessage.error('题目语言缺失，无法开始')
    return
  }
  const payload = {
    id: String(p.taskId || ''),
    title: String(p.title || ''),
    description: String(p.description || ''),
    language: lang,
    starterCode: String(p.starterCode || ''),
    expectedOutput: String(p.expectedOutput || ''),
    solutionCode: '',
    isTeacherTask: false,
    isCompetition: true,
    competitionId: String(competitionId.value || ''),
    competitionName: String(competition.value?.name || '')
  }
  sessionStorage.setItem('dailyPractice', JSON.stringify(payload))
  return morphNavigation(event?.currentTarget?.closest('tr') || event?.currentTarget,()=>router.push(`/learn/${lang}`),routeDestination('.exercise-brief'))
}

const init = async () => {
  loading.value = true
  errorMessage.value = ''
  showRegisterAction.value = false
  try {
    const user = getCurrentUser()
    if (!user?.id) {
      errorMessage.value = '请先登录后再进入比赛'
      showRegisterAction.value = false
      return
    }
    await loadCompetition()
    if (competition.value?.mode === 'problem_set') {
      await loadProblems()
      await loadMySubmissions()
    } else {
      problems.value = []
      mySubmissions.value = new Map()
    }
    if (competition.value?.status === 'ended') {
      await loadMyResult()
    } else {
      myResult.value = null
    }
  } catch (e) {
    const status = e?.response?.status
    if (status === 403) {
      const msg = e?.response?.data?.detail || e?.response?.data?.message
      if (msg) {
        errorMessage.value = String(msg)
        showRegisterAction.value = String(msg).includes('报名')
      } else {
        errorMessage.value = '请先报名后再进入比赛'
        showRegisterAction.value = true
      }
    } else if (status === 401) {
      errorMessage.value = '登录已过期，请重新登录'
      showRegisterAction.value = false
    } else {
      errorMessage.value = e?.message || '加载失败'
      showRegisterAction.value = false
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  init()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f6f7fb;
}

.topbar {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 18px 20px;
  background: white;
  border-bottom: 1px solid #ebeef5;
}

.title {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.name {
  font-size: 18px;
  font-weight: 700;
  color: #303133;
}

.meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  color: #606266;
  font-size: 13px;
}

.meta-item {
  color: #606266;
}

.content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px;
}

.loading {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.info-layout {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 18px;
  align-items: start;
}

.info-main,
.info-side {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.info-card {
  border-radius: 12px;
}

.card-title {
  font-weight: 700;
  color: #303133;
}

.desc {
  color: #303133;
  line-height: 1.7;
  white-space: pre-wrap;
}

.list {
  margin: 0;
  padding-left: 18px;
  color: #303133;
  line-height: 1.8;
}

.tags {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  margin: 0;
}

.group {
  margin-top: 18px;
}

.group-title {
  display: flex;
  gap: 8px;
  align-items: baseline;
  margin: 0 0 10px;
  font-weight: 700;
  color: #303133;
}

.group-count {
  color: #909399;
  font-weight: 400;
  font-size: 12px;
}
.test-play-page .info-card{animation:test-paper-in 520ms cubic-bezier(.16,1,.3,1) both}.test-play-page .info-card:nth-child(2){animation-delay:70ms}.test-play-page .info-card:nth-child(3){animation-delay:140ms}@keyframes test-paper-in{from{opacity:0;translate:0 18px}to{opacity:1;translate:0 0}}
</style>

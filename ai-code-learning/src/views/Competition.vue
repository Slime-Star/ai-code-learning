<template>
  <div class="competition-page">
    <!-- 顶部横幅 -->
    <div class="hero-banner">
      <div class="banner-content">
        <div class="banner-left">
          <h1 class="banner-title">🏆 班级测试</h1>
          <p class="banner-subtitle">一次测试，一次突破，一次更好的自己！</p>
          <div class="banner-stats">
            <div class="stat-item">
              <span class="stat-number">{{ competitions.length }}</span>
              <span class="stat-label">测试总数</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ ongoingCount }}</span>
              <span class="stat-label">进行中</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ registeringCount }}</span>
              <span class="stat-label">报名中</span>
            </div>
          </div>
        </div>
        <div class="banner-right"><ContentBoundary silent><TestFlowScene :status="activeTab" @select="activeTab = $event" /></ContentBoundary></div>
      </div>
    </div>

    <!-- 筛选标签 -->
    <div class="filter-section">
      <div class="filter-container">
        <div class="filter-tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id"
          >
            {{ tab.icon }} {{ tab.name }}
          </button>
        </div>
        <div class="search-box">
          <el-input
            v-model="searchQuery"
            placeholder="搜索测试..."
            prefix-icon="Search"
            clearable
          />
        </div>
      </div>
    </div>

    <!-- 测试卡片列表 -->
    <div class="competition-container">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
      
      <div v-else class="competition-grid">
        <div 
          v-for="comp in filteredCompetitions" 
          :key="comp.id"
          class="competition-card" @pointerenter="warmMotionRoute(router, `/competition/${comp.id}`)" @focusin="warmMotionRoute(router, `/competition/${comp.id}`)" :data-motion-key="`competition:${comp.id}`"
          :class="['status-' + comp.status]"
        >
          <div class="card-header">
            <div class="status-badge">
              <span :class="['dot', comp.status]"></span>
              {{ getStatusText(comp.status) }}
            </div>
            <div class="competition-type">{{ getTypeText(comp.type) }}</div>
          </div>
          
          <div class="card-body">
            <h3 class="competition-name">{{ comp.name }}</h3>
            <p class="competition-desc">{{ comp.desc }}</p>
            
            <div class="info-row">
              <div class="info-item">
                <el-icon><Trophy /></el-icon>
                <span>{{ comp.difficulty }}</span>
              </div>
              <div class="info-item">
                <el-icon><User /></el-icon>
                <span>{{ comp.participants }}人</span>
              </div>
              <div class="info-item">
                <el-icon><Clock /></el-icon>
                <span>{{ comp.duration }}</span>
              </div>
            </div>

            <div class="time-info">
              <div class="time-item">
                <span class="time-label">报名时间</span>
                <span class="time-value">{{ comp.registerTime }}</span>
              </div>
              <div class="time-item">
                <span class="time-label">比赛时间</span>
                <span class="time-value">{{ comp.competitionTime }}</span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <el-tag 
              v-for="tag in comp.tags.slice(0, 3)" 
              :key="tag"
              size="small"
              class="tag"
            >
              {{ tag }}
            </el-tag>
            <div class="footer-actions">
              <el-button size="small" @click="showDetail(comp)">详情</el-button>
              <el-button 
                v-if="comp.status === 'registering'"
                type="primary" 
                size="small"
                :disabled="!!comp.myRegistered || (comp.registerValid && !comp.canRegister)"
                @click="register(comp)"
              >
                {{
                  comp.myRegistered
                    ? '已报名'
                    : (comp.registerValid && !comp.canRegister
                        ? (comp.registerReason === 'not_started' ? '未到报名' : (comp.registerReason === 'ended' ? '报名已结束' : '不可报名'))
                        : '立即报名')
                }}
              </el-button>
              <el-button 
                v-else-if="comp.status === 'ongoing'"
                type="success" 
                size="small"
                :disabled="comp.competitionValid && !comp.canEnter"
                @click="enter(comp, $event)"
              >
                {{ getEnterBtnText(comp) }}
              </el-button>
            </div>
          </div>
        </div>
        <CompetitionSketch v-if="filteredCompetitions.length > 0 && filteredCompetitions.length % 2 === 1" class="competition-gap-art" variant="target" />
      </div>

      <div v-if="!loading && filteredCompetitions.length === 0" class="competition-empty-scene"><el-empty description="暂无相关测试" /><CompetitionSketch variant="target" /></div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      :title="currentComp?.name"
      width="700px"
      class="detail-dialog"
    >
      <div v-if="currentComp" class="detail-content">
        <div class="detail-header">
          <el-tag :type="getTagType(currentComp.status)" size="large">
            {{ getStatusText(currentComp.status) }}
          </el-tag>
          <el-tag type="info" size="large">{{ getTypeText(currentComp.type) }}</el-tag>
        </div>

        <div class="detail-section">
          <h4>📋 测试简介</h4>
          <p>{{ currentComp.detailDesc }}</p>
        </div>

        <div class="detail-section">
          <h4>📖 测试规则</h4>
          <ul>
            <li v-for="(rule, idx) in currentComp.rules" :key="idx">{{ rule }}</li>
          </ul>
        </div>

        <div class="detail-section" v-if="currentComp.rewards?.length">
          <h4>🎁 奖项设置</h4>
          <ul>
            <li v-for="(reward, idx) in currentComp.rewards" :key="idx">{{ reward }}</li>
          </ul>
        </div>

        <div class="detail-section" v-if="currentComp.status === 'ended'">
          <h4>📊 我的成绩</h4>
          <div class="detail-info-grid">
            <div class="info-box">
              <div class="info-label">我的得分</div>
              <div class="info-value">
                <span v-if="myResult">{{ myResult.score }} / {{ myResult.maxScore }}</span>
                <span v-else>—</span>
              </div>
            </div>
            <div class="info-box">
              <div class="info-label">我的名次</div>
              <div class="info-value">
                <span v-if="myResult">{{ myResult.rank }} / {{ myResult.totalParticipants }}</span>
                <span v-else>—</span>
              </div>
            </div>
            <div class="info-box">
              <div class="info-label">操作</div>
              <div class="info-value">
                <el-button size="small" plain :loading="myResultLoading" :disabled="myResultLoading" @click="loadMyResult(currentComp)">
                  刷新成绩
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-info-grid">
          <div class="info-box">
            <div class="info-label">难度</div>
            <div class="info-value">{{ currentComp.difficulty }}</div>
          </div>
          <div class="info-box">
            <div class="info-label">参赛人数</div>
            <div class="info-value">{{ currentComp.participants }}人</div>
          </div>
          <div class="info-box">
            <div class="info-label">比赛时长</div>
            <div class="info-value">{{ currentComp.duration }}</div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailVisible = false">关闭</el-button>
          <el-button 
            v-if="currentComp?.status === 'registering'"
            type="primary"
            :disabled="!!currentComp?.myRegistered || (currentComp?.registerValid && !currentComp?.canRegister)"
            @click="register(currentComp)"
          >
            {{
              currentComp?.myRegistered
                ? '已报名'
                : (currentComp?.registerValid && !currentComp?.canRegister
                    ? (currentComp?.registerReason === 'not_started' ? '未到报名' : (currentComp?.registerReason === 'ended' ? '报名已结束' : '不可报名'))
                    : '立即报名')
            }}
          </el-button>
          <el-button 
            v-else-if="currentComp?.status === 'ongoing'"
            type="success"
            :disabled="currentComp?.competitionValid && !currentComp?.canEnter"
            @click="enter(currentComp, $event)"
          >
            {{ getEnterBtnText(currentComp) }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <div class="competition-ornaments"><CompetitionSketch variant="timer" /><CompetitionSketch variant="flags" /></div>
  </div>
</template>

<script setup>
import {morphNavigation,routeDestination,findMotionElement,takeMotionList,warmMotionRoute,seedMotionPage,afterSharedNavigation} from '@/utils/sharedMotion'
import CompetitionSketch from '@/components/CompetitionSketch.vue'
import ContentBoundary from '@/components/ContentBoundary.vue'
import TestFlowScene from '@/components/TestFlowScene.vue'
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Trophy, User, Clock, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getAuthToken, getCurrentUser } from '@/utils/authStorage'

// 本地示例数据
const localCompetitions = [
  {
    id: 1,
    name: '2026全国大学生程序设计大赛',
    desc: '面向全国大学生的算法测试，考察数据结构与算法能力！',
    type: 'algorithm',
    status: 'registering',
    difficulty: '中等',
    participants: 1256,
    duration: '4小时',
    registerTime: '05-01 ~ 05-30',
    competitionTime: '06-10 09:00 ~ 13:00',
    tags: ['算法', '数据结构', '大学生', 'ACM'],
    detailDesc: '本次测试旨在培养和提高大学生的程序设计与算法分析能力，测试题目涵盖数组、链表、树、图等数据结构。',
    rules: [
      '比赛时长为4小时，共8道题目',
      '可以使用C++、Java、Python、JavaScript四种语言',
      '禁止使用任何网络资源'
    ],
    rewards: [
      '一等奖：5名，奖金5000元 + 荣誉证书',
      '二等奖：10名，奖金3000元 + 荣誉证书',
      '三等奖：20名，奖金1000元 + 荣誉证书'
    ]
  },
  {
    id: 2,
    name: 'Web应用开发挑战赛',
    desc: '以实际项目为导向的Web开发测试，48小时内完成一个功能完整的应用！',
    type: 'web',
    status: 'ongoing',
    difficulty: '较难',
    participants: 892,
    duration: '48小时',
    registerTime: '04-15 ~ 05-15',
    competitionTime: '05-20 00:00 ~ 05-22 00:00',
    tags: ['Web开发', '前端', '后端', '全栈'],
    detailDesc: '本次测试要求选手在48小时内完成一个功能完整、设计美观的Web应用，包含用户系统、数据管理等模块。',
    rules: [
      '比赛时长为48小时',
      '前端框架不限，推荐使用Vue或React',
      '需要提交完整的代码和演示文档'
    ],
    rewards: [
      '最佳应用奖：1名，奖金8000元',
      '最佳设计奖：1名，奖金5000元'
    ]
  },
  {
    id: 3,
    name: 'Python数据科学测试',
    desc: '数据处理与分析测试，考察数据分析、机器学习、可视化等能力！',
    type: 'data',
    status: 'registering',
    difficulty: '中等',
    participants: 567,
    duration: '72小时',
    registerTime: '05-10 ~ 06-10',
    competitionTime: '06-15 00:00 ~ 06-18 00:00',
    tags: ['Python', '数据科学', '机器学习'],
    detailDesc: '本次测试围绕真实数据集展开，选手需要完成数据清洗、特征工程、模型训练、结果可视化等完整流程。',
    rules: [
      '比赛时长72小时',
      '使用Python语言，可使用numpy、pandas等库',
      '需要提交完整的分析报告和代码'
    ],
    rewards: [
      '一等奖：1名，奖金6000元',
      '二等奖：3名，奖金3000元'
    ]
  }
]

const restoredList=takeMotionList('/competition',getCurrentUser()?.id || 'guest')
const activeTab = ref(restoredList?.tab || 'all')
const searchQuery = ref(restoredList?.query || '')
const detailVisible = ref(false)
const currentComp = ref(null)
const myResultLoading = ref(false)
const myResult = ref(null)
const loading = ref(!restoredList?.competitions?.length)
const competitions = ref(restoredList?.competitions || [...localCompetitions])
const myRegistrationIds = ref(new Set(restoredList?.registrations || []))

const router = useRouter()

const tabs = [
  { id: 'all', name: '全部', icon: '🏠' },
  { id: 'registering', name: '报名中', icon: '✍️' },
  { id: 'ongoing', name: '进行中', icon: '🚀' },
  { id: 'ended', name: '已结束', icon: '✅' }
]

const filteredCompetitions = computed(() => {
  let result = competitions.value
  
  if (activeTab.value !== 'all') {
    result = result.filter(c => c.status === activeTab.value)
  }
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(c => 
      c.name.toLowerCase().includes(query) || 
      c.desc.toLowerCase().includes(query) ||
      c.tags.some(t => t.toLowerCase().includes(query))
    )
  }
  
  return result
})

const ongoingCount = computed(() => competitions.value.filter(c => c.status === 'ongoing').length)
const registeringCount = computed(() => competitions.value.filter(c => c.status === 'registering').length)

const loadCompetitions = async () => {
  loading.value = !competitions.value.length || !restoredList
  try {
    const res = await request.get('/api/competitions', {
      params: {
        status: activeTab.value === 'all' ? null : activeTab.value,
        search: searchQuery.value
      }
    })
    if (res?.success && Array.isArray(res.data)) {
      competitions.value = res.data
    }
    applyMyRegistrationFlags()
  } catch (err) {
    console.log('API加载失败，使用本地数据:', err)
    applyMyRegistrationFlags()
  } finally {
    loading.value = false
  }
}

let stopReturnRefresh
onMounted(() => {
  const refresh=async()=>{await refreshMyRegistrations();await loadCompetitions()}
  if(restoredList)stopReturnRefresh=afterSharedNavigation(refresh)
  else refresh()
})
onBeforeUnmount(()=>stopReturnRefresh?.())

watch(activeTab, () => loadCompetitions())
watch(searchQuery, (val) => {
  setTimeout(() => loadCompetitions(), 300)
})

const refreshMyRegistrations = async () => {
  const token = getAuthToken()
  const user = getCurrentUser()
  if (!token || !user?.id || user?.role !== 'student') {
    myRegistrationIds.value = new Set()
    applyMyRegistrationFlags()
    return
  }
  try {
    const res = await request.get('/api/competitions/my-registrations')
    const ids = Array.isArray(res?.competitionIds) ? res.competitionIds : []
    myRegistrationIds.value = new Set(ids.map((x) => Number(x)))
    applyMyRegistrationFlags()
  } catch {
    myRegistrationIds.value = new Set()
    applyMyRegistrationFlags()
  }
}

const getLocalRegistrationKey = (userId, competitionId) => `competition_registered_${String(userId || '')}_${String(competitionId || '')}`

const markRegisteredLocal = (competitionId) => {
  const user = getCurrentUser()
  if (!user?.id) return
  try {
    localStorage.setItem(getLocalRegistrationKey(user.id, competitionId), '1')
  } catch {
  }
}

const hasRegisteredLocal = (competitionId) => {
  const user = getCurrentUser()
  if (!user?.id) return false
  try {
    return localStorage.getItem(getLocalRegistrationKey(user.id, competitionId)) === '1'
  } catch {
    return false
  }
}

const applyMyRegistrationFlags = () => {
  const ids = myRegistrationIds.value || new Set()
  competitions.value = (competitions.value || []).map((c) => ({
    ...c,
    myRegistered: ids.has(Number(c.id)) || hasRegisteredLocal(c.id)
  }))
  if (currentComp.value?.id) {
    const latest = competitions.value.find((c) => c.id === currentComp.value.id)
    if (latest) currentComp.value = latest
  }
}

const markRegisteredUI = (competitionId) => {
  myRegistrationIds.value.add(Number(competitionId))
  markRegisteredLocal(competitionId)
  competitions.value = (competitions.value || []).map((c) =>
    Number(c.id) === Number(competitionId) ? { ...c, myRegistered: true } : c
  )
  if (currentComp.value?.id && Number(currentComp.value.id) === Number(competitionId)) {
    currentComp.value = { ...currentComp.value, myRegistered: true }
  }
}

const register = async (comp) => {
  try {
    const currentUser = getCurrentUser()
    if (!currentUser?.id) {
      ElMessage.warning('请先登录后再报名')
      detailVisible.value = false
      return false
    }

    if (comp?.myRegistered) {
      ElMessage.info('你已报名该测试')
      detailVisible.value = false
      return true
    }

    if (comp?.registerValid && !comp?.canRegister) {
      const reason = String(comp?.registerReason || '')
      ElMessage.warning(reason === 'not_started' ? '未到报名时间' : reason === 'ended' ? '报名时间已结束' : '暂不可报名')
      return false
    }
    
    const res = await request.post('/api/competitions/register', {
      competitionId: comp.id,
      competitionName: comp.name,
      userId: currentUser.id,
      userName: currentUser.name,
      competition_id: comp.id,
      competition_name: comp.name,
      user_id: currentUser.id,
      user_name: currentUser.name
    })
    
    // 本地更新报名人数
    const index = competitions.value.findIndex(c => c.id === comp.id)
    if (index !== -1) {
      markRegisteredUI(comp.id)
      if (res?.created) {
        competitions.value[index].participants += 1
      }
    }
    
    ElMessage.success(res?.message || `成功报名「${comp.name}」！`)
    detailVisible.value = false
    return true
  } catch (err) {
    const serverMsg = err?.response?.data?.detail || err?.response?.data?.message
    if (serverMsg) {
      ElMessage.error(String(serverMsg))
      return false
    }
    const msg = String(err?.message || '')
    if (msg.includes('已经报名') || msg.includes('已报名')) {
      markRegisteredUI(comp?.id)
      ElMessage.info('你已报名该测试')
      detailVisible.value = false
      return true
    }
    console.error('报名失败:', err)
    ElMessage.error('报名失败，请重试')
    return false
  }
}

const getEnterBtnText = (comp) => {
  if (comp?.competitionValid && !comp?.canEnter) {
    const reason = String(comp?.competitionReason || '')
    return reason === 'not_started' ? '未到作答' : reason === 'ended' ? '作答已结束' : '暂不可进入'
  }
  return comp?.myRegistered ? '进入比赛' : '报名并进入'
}

const enter = async (comp, event) => {
  const source=event?.currentTarget?.closest('.competition-card') || findMotionElement(`competition:${comp.id}`) || event?.currentTarget
  const currentUser = getCurrentUser()
  if (!currentUser?.id) {
    ElMessage.warning('请先登录后再进入比赛')
    return
  }

  if (comp?.competitionValid && !comp?.canEnter) {
    const reason = String(comp?.competitionReason || '')
    ElMessage.warning(reason === 'not_started' ? '未到作答时间' : reason === 'ended' ? '作答时间已结束' : '暂不可进入比赛')
    return
  }

  let ok = true
  if (!comp?.myRegistered) {
    ok = await register(comp)
  }
  if (!ok) return

  seedMotionPage(`/competition/${comp.id}`,currentUser.id,{...comp})
  detailVisible.value = false
  return morphNavigation(source,()=>router.push(`/competition/${comp.id}`),routeDestination('.topbar .title'),{remember:'test',from:router.currentRoute.value.fullPath,state:{owner:currentUser.id,tab:activeTab.value,query:searchQuery.value,competitions:competitions.value,registrations:[...myRegistrationIds.value]}})
}

const getStatusText = (status) => {
  const map = { registering: '报名中', ongoing: '进行中', ended: '已结束' }
  return map[status] || status
}

const getTypeText = (type) => {
  const map = {
    algorithm: '算法测试',
    web: 'Web开发',
    data: '数据科学',
    ai: '人工智能',
    mobile: '移动开发',
    game: '游戏开发'
  }
  return map[type] || type
}

const getTagType = (status) => {
  const map = { registering: 'success', ongoing: 'warning', ended: 'info' }
  return map[status] || ''
}

const showDetail = (comp) => {
  currentComp.value = comp
  detailVisible.value = true
  myResult.value = null
  if (String(comp?.status || '') === 'ended') {
    loadMyResult(comp)
  }
}

const loadMyResult = async (comp) => {
  const id = Number(comp?.id || 0)
  if (!id) return
  if (myResultLoading.value) return
  myResultLoading.value = true
  try {
    const res = await request.get(`/api/competitions/${id}/my-result`)
    myResult.value = res?.result || null
  } catch {
    myResult.value = null
  } finally {
    myResultLoading.value = false
  }
}
</script>

<style scoped>
.competition-ornaments { max-width: 1152px; margin: 0 auto; padding: 12px 24px 30px; display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); align-items: center; gap: 70px; }
.competition-empty-scene { display: flex; justify-content: center; align-items: center; gap: 60px; }
.competition-empty-scene :deep(.competition-sketch) { max-width: 300px; margin: 0; }
.competition-gap-art { align-self: center; }
@media (max-width: 900px) { .competition-gap-art { display: none; }.competition-ornaments { gap: 10px; padding: 8px 16px 24px; }.competition-empty-scene { flex-direction: column; gap: 0; }.competition-empty-scene :deep(.competition-sketch) { max-width: 210px; } }
.competition-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f5f7fa 0%, #e8ecf1 100%);
}

.hero-banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 60px 0;
  color: white;
}

.banner-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 40px;
}

.banner-title {
  font-size: 42px;
  font-weight: 800;
  margin: 0 0 16px;
}

.banner-subtitle {
  font-size: 18px;
  opacity: 0.95;
  margin: 0 0 28px;
}

.banner-stats {
  display: flex;
  gap: 32px;
}

.stat-number {
  font-size: 32px;
  font-weight: 800;
}

.stat-label {
  font-size: 14px;
  opacity: 0.85;
}

.banner-right {
  display: flex;
  gap: 16px;
}

.feature-card {
  background: rgba(255,255,255,0.15);
  padding: 20px 24px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.feature-icon {
  font-size: 32px;
}

.feature-text {
  font-size: 14px;
  font-weight: 600;
}

.filter-section {
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.filter-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
}

.filter-tabs {
  display: flex;
  gap: 12px;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  background: #f0f2f5;
  border-radius: 24px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 500;
}

.tab-btn:hover {
  background: #e0e6ed;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.search-box {
  width: 320px;
}

.competition-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.competition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 24px;
}

.competition-card {
  background: white;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
}

.competition-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 28px rgba(0,0,0,0.12);
}

.competition-card.status-registering {
  border-top: 4px solid #67c23a;
}

.competition-card.status-ongoing {
  border-top: 4px solid #e6a23c;
}

.competition-card.status-ended {
  border-top: 4px solid #909399;
}

.card-header {
  display: flex;
  justify-content: space-between;
  padding: 18px 20px 10px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.registering {
  background: #67c23a;
  animation: pulse 1.5s infinite;
}

.dot.ongoing {
  background: #e6a23c;
  animation: pulse 1.5s infinite;
}

.dot.ended {
  background: #909399;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.competition-type {
  font-size: 12px;
  color: #909399;
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 12px;
}

.card-body {
  padding: 0 20px 16px;
  flex: 1;
}

.competition-name {
  font-size: 18px;
  font-weight: 700;
  margin: 0 0 10px;
  color: #1f2937;
}

.competition-desc {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 14px;
}

.info-row {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #6b7280;
}

.time-info {
  background: #f8fafc;
  padding: 12px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.time-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
}

.time-label {
  color: #909399;
}

.time-value {
  color: #374151;
  font-weight: 500;
}

.card-footer {
  padding: 14px 20px 18px;
  border-top: 1px solid #f0f0f0;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 12px;
}

.tag {
  margin-right: 8px;
  margin-bottom: 6px;
}

.detail-content {
  padding-top: 10px;
}

.detail-header {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  font-size: 16px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 12px;
}

.detail-section p {
  color: #4b5563;
  line-height: 1.8;
  margin: 0;
}

.detail-section ul {
  margin: 0;
  padding-left: 20px;
}

.detail-section li {
  color: #4b5563;
  line-height: 1.8;
  margin-bottom: 6px;
}

.detail-info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-box {
  background: #f8fafc;
  padding: 16px;
  border-radius: 12px;
  text-align: center;
}

.info-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.info-value {
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 900px) {
  .banner-content {
    flex-direction: column;
    text-align: center;
  }
  
  .banner-stats {
    justify-content: center;
  }
  
  .filter-container {
    flex-direction: column;
  }
  
  .filter-tabs {
    width: 100%;
    overflow-x: auto;
    padding-bottom: 6px;
  }
  
  .search-box {
    width: 100%;
  }
  
  .competition-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-info-grid {
    grid-template-columns: 1fr;
  }
}
.banner-right { min-width: 0; flex-shrink: 0; width: 430px; max-width: 100%; }
@media(max-width:950px){.banner-content{flex-direction:column;align-items:center;gap:16px}.banner-left{text-align:center}.banner-stats{justify-content:center}.banner-right{justify-content:center}}
</style>

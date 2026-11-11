<template>
  <div class="teacher-competition-page">
    <div class="hero-banner">
      <div class="banner-content">
        <div class="banner-left">
          <h1 class="banner-title">🏆 测试管理</h1>
          <p class="banner-subtitle">发布测试、查看提交、连续批改，让反馈及时回到学生手中。</p>
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
        <div class="banner-right">
          <TeacherScene scene="pipeline" />

        </div>
      </div>
    </div>
 
    <el-alert v-if="route.query.review==='pending'" class="pending-review-hint" title="已启用待批改筛选：打开测试详情，点击“提交情况”进入批改。" type="info" :closable="false" show-icon />
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
        <div class="actions">
          <el-input
            v-model="searchQuery"
            placeholder="搜索测试..."
            prefix-icon="Search"
            clearable
            class="search-box"
          />
          <el-button class="publish-btn" type="primary" @click="openPublish">发布测试</el-button>
          <el-button class="refresh-btn" plain @click="loadCompetitions">刷新</el-button>
        </div>
      </div>
    </div>
 
    <div class="competition-container">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>加载中...</p>
      </div>
 
      <div v-else class="competition-grid">
        <div
          v-for="comp in filteredCompetitions"
          :key="comp.id"
          class="competition-card"
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
            <el-tag v-for="tag in comp.tags.slice(0, 3)" :key="tag" size="small" class="tag">
              {{ tag }}
            </el-tag>
            <div class="footer-actions">
              <el-button size="small" @click="showDetail(comp)">详情</el-button>
            </div>
          </div>
        </div>
      </div>
 
      <el-empty v-if="!loading && filteredCompetitions.length === 0" description="暂无相关测试" />
    </div>
 
    <el-dialog v-model="detailVisible" :title="currentComp?.name" width="700px" class="detail-dialog">
      <div v-if="currentComp" class="detail-content">
        <div class="detail-header">
          <el-tag :type="getTagType(currentComp.status)" size="large">{{ getStatusText(currentComp.status) }}</el-tag>
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
          <el-button v-if="currentComp?.mode === 'problem_set'" @click="openSubmissions">提交情况/批改</el-button>
          <el-button v-if="currentComp?.status !== 'ended'" type="danger" @click="endCompetition">提前终止</el-button>
          <el-button @click="detailVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog v-model="submissionsVisible" :title="`提交情况：${currentComp?.name || ''}`" width="980px">
      <div class="submission-tools"><el-input v-model="submissionQuery" placeholder="搜索学生或题目" clearable /><el-radio-group v-model="submissionScope"><el-radio-button value="all">全部提交</el-radio-button><el-radio-button value="pending">待批改 {{ pendingSubmissions.length }}</el-radio-button></el-radio-group><el-button :loading="submissionsLoading" @click="loadSubmissions">刷新</el-button></div>
      <el-alert v-if="submissionError" :title="submissionError" type="error" :closable="false" />
      <el-table :data="visibleSubmissions" border style="width: 100%" v-loading="submissionsLoading" :empty-text="submissionScope==='pending'?'暂无待批改提交':'暂无提交记录'">
        <el-table-column prop="userName" label="学生" width="140" />
        <el-table-column prop="taskTitle" label="题目" min-width="220" />
        <el-table-column prop="points" label="分值" width="90" />
        <el-table-column label="提交时间" min-width="170">
          <template #default="{ row }">
            {{ row.submittedAt ? row.submittedAt : '未提交' }}
          </template>
        </el-table-column>
        <el-table-column label="自动判定" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.submittedAt" :type="row.passed ? 'success' : 'warning'" size="small">
              {{ row.passed ? '通过' : '未通过' }}
            </el-tag>
            <el-tag v-else type="info" size="small">—</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="批改分数" width="110">
          <template #default="{ row }">
            <span v-if="row.score !== null && row.score !== undefined">{{ row.score }}</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.submittedAt && (row.score !== null && row.score !== undefined)" type="success" size="small">已批改</el-tag>
            <el-tag v-else-if="row.submittedAt" type="warning" size="small">待批改</el-tag>
            <el-tag v-else type="info" size="small">未提交</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" :disabled="!row.submittedAt" @click="openGrade(row)">查看/批改</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="submissionsVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="gradeVisible" title="批改工作区" size="min(1060px,96vw)" append-to-body class="teacher-drawer grading-drawer" :close-on-click-modal="false" :before-close="beforeGradeClose">
      <template v-if="gradeTarget">
        <div class="grade-heading"><div><span class="grade-eyebrow">READ · REVIEW · RESPOND</span><h2>{{ gradeTarget.userName }} <small>／ {{ gradeTarget.taskTitle }}</small></h2></div><el-tag :type="gradeTarget.passed?'success':'warning'">自动判定：{{ gradeTarget.passed?'通过':'未通过' }}</el-tag></div>
        <div class="grade-layout">
          <div class="grade-reading"><section><div class="grade-section-heading"><h3>学生代码</h3><span>{{ gradeTarget.language || '代码提交' }}</span></div><pre class="grade-code"><code>{{ gradeTarget.code || '暂无代码' }}</code></pre></section><section class="grade-output"><h3>运行结果</h3><pre>{{ gradeTarget.output || '无输出' }}</pre><template v-if="gradeTarget.error"><h3>错误信息</h3><pre class="grade-error">{{ gradeTarget.error }}</pre></template></section></div>
          <aside class="grade-assessment"><div class="grade-max"><span>本题满分</span><strong>{{ gradeTarget.points }} <small>分</small></strong></div><el-form label-position="top"><el-form-item label="批改分数"><el-input-number v-model="gradeScore" :min="0" :max="Number(gradeTarget.points || 0)" :step="1" :precision="0" :disabled="gradeSaving" controls-position="right" /></el-form-item><el-form-item label="评语与学习建议"><el-input v-model="gradeFeedback" type="textarea" :rows="8" :disabled="gradeSaving" placeholder="写下扣分原因，或给学生下一步练习建议" /></el-form-item></el-form><div class="grade-next"><span>待批改 {{ pendingSubmissions.length }} 份</span><p>{{ nextUngraded?`下一份：${nextUngraded.userName} · ${nextUngraded.taskTitle}`:'当前没有其他待批改提交' }}</p></div></aside>
        </div>
      </template>
      <template #footer><div class="grade-footer"><el-button :disabled="gradeSaving" @click="beforeGradeClose(()=>gradeVisible=false)">返回提交列表</el-button><span></span><el-button :loading="gradeSaving" :disabled="gradeSaving" @click="saveGrade(false)">保存并返回</el-button><el-button type="primary" :loading="gradeSaving" :disabled="gradeSaving" @click="saveGrade(true)">{{ nextUngraded?'保存并查看下一份':'保存并完成批改' }}</el-button></div></template>
    </el-drawer>

    <el-dialog v-model="publishVisible" title="发布测试" width="760px">
      <el-form :model="publishForm" label-width="92px">
        <el-form-item label="名称">
          <el-input v-model="publishForm.name" placeholder="请输入测试名称" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="publishForm.desc" placeholder="一句话介绍测试" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="publishForm.type" style="width: 100%">
            <el-option label="算法测试" value="algorithm" />
            <el-option label="Web开发" value="web" />
            <el-option label="数据科学" value="data" />
            <el-option label="人工智能" value="ai" />
            <el-option label="移动开发" value="mobile" />
            <el-option label="游戏开发" value="game" />
          </el-select>
        </el-form-item>
        <el-form-item label="模式">
          <el-select v-model="publishForm.mode" style="width: 100%">
            <el-option label="普通测试" value="general" />
            <el-option label="做题测试" value="problem_set" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="publishForm.status" style="width: 100%">
            <el-option label="报名中" value="registering" />
            <el-option label="进行中" value="ongoing" />
            <el-option label="已结束" value="ended" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="publishForm.difficulty" style="width: 100%">
            <el-option label="简单" value="简单" />
            <el-option label="中等" value="中等" />
            <el-option label="较难" value="较难" />
            <el-option label="困难" value="困难" />
          </el-select>
        </el-form-item>
        <el-form-item label="时长">
          <el-input v-model="publishForm.duration" placeholder="如：4小时 / 48小时" />
        </el-form-item>
        <el-form-item label="报名时间">
          <el-date-picker
            v-model="registerRange"
            type="daterange"
            unlink-panels
            range-separator="~"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :locale="zhCn"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="比赛时间">
          <el-date-picker
            v-model="competitionRange"
            type="datetimerange"
            unlink-panels
            range-separator="~"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :locale="zhCn"
            value-format="YYYY-MM-DD HH:mm"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="publishForm.tags" placeholder="用逗号分隔，如：算法,数据结构,ACM" />
        </el-form-item>
        <template v-if="publishForm.mode === 'problem_set'">
          <el-form-item label="题目">
            <el-select
              v-model="publishForm.task_ids"
              multiple
              filterable
              :loading="tasksLoading"
              style="width: 100%"
              placeholder="选择要加入测试的题目（来自你发布的班级题目）"
            >
              <el-option
                v-for="t in teacherTasks"
                :key="t.id"
                :label="`${t.title}（${t.class_name || '班级'}）`"
                :value="t.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="分类/分值">
            <el-table v-if="publishForm.problems.length" :data="publishForm.problems" size="small" style="width: 100%">
              <el-table-column prop="title" label="题目" min-width="220" />
              <el-table-column label="分类" min-width="140">
                <template #default="{ row }">
                  <el-input v-model="row.category" placeholder="如：图论/DP/字符串" />
                </template>
              </el-table-column>
              <el-table-column label="分值" width="120">
                <template #default="{ row }">
                  <el-input v-model.number="row.points" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="90">
                <template #default="{ row }">
                  <el-button size="small" type="danger" plain @click="removeProblem(row.task_id)">移除</el-button>
                </template>
              </el-table-column>
            </el-table>
            <div v-else class="empty-hint">先在上面选择题目</div>
          </el-form-item>
        </template>
        <el-form-item label="详情">
          <el-input v-model="publishForm.detail_desc" type="textarea" :rows="3" placeholder="测试详情介绍" />
        </el-form-item>
        <el-form-item label="规则">
          <el-input v-model="publishForm.rules" type="textarea" :rows="4" placeholder="每行一条规则" />
        </el-form-item>
        <el-form-item label="积分奖项">
          <div style="display: grid; gap: 10px; width: 100%">
            <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap">
              <el-switch v-model="usePointsRewards" active-text="开启" inactive-text="关闭" />
              <span style="color: #666; font-size: 12px">开启后将自动生成“奖项”内容，单位为平台积分</span>
            </div>
            <div v-if="usePointsRewards" style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px">
              <el-input-number v-model="pointsRewards.first" :min="0" :max="100000" controls-position="right" style="width: 100%">
                <template #prefix>一等奖</template>
                <template #suffix>积分</template>
              </el-input-number>
              <el-input-number v-model="pointsRewards.second" :min="0" :max="100000" controls-position="right" style="width: 100%">
                <template #prefix>二等奖</template>
                <template #suffix>积分</template>
              </el-input-number>
              <el-input-number v-model="pointsRewards.third" :min="0" :max="100000" controls-position="right" style="width: 100%">
                <template #prefix>三等奖</template>
                <template #suffix>积分</template>
              </el-input-number>
              <el-input-number v-model="pointsRewards.participation" :min="0" :max="100000" controls-position="right" style="width: 100%">
                <template #prefix>参与奖</template>
                <template #suffix>积分</template>
              </el-input-number>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="奖项">
          <el-input v-model="publishForm.rewards" type="textarea" :rows="3" placeholder="每行一条奖项" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="publishVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishing" @click="publish">发布</el-button>
      </template>
    </el-dialog>
    <TopicArt scene="trophy" inverse />
  </div>
</template>
 
<script setup>
import TopicArt from '@/components/TopicArt.vue'
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import {useRoute,onBeforeRouteLeave} from 'vue-router'
import TeacherScene from '@/components/TeacherScene.vue'
import {isUngraded} from '@/utils/teacherApi'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Trophy, User, Clock, Loading } from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import axios from 'axios'
import { getAuthToken } from '@/utils/authStorage'
 
const route=useRoute()
const activeTab = ref('all')
const searchQuery = ref('')
const detailVisible = ref(false)
const currentComp = ref(null)
const loading = ref(true)
const competitions = ref([])
 
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
      String(c.name || '').toLowerCase().includes(query) ||
      String(c.desc || '').toLowerCase().includes(query) ||
      (Array.isArray(c.tags) ? c.tags : []).some(t => String(t || '').toLowerCase().includes(query))
    )
  }
  return result
})
 
const ongoingCount = computed(() => competitions.value.filter(c => c.status === 'ongoing').length)
const registeringCount = computed(() => competitions.value.filter(c => c.status === 'registering').length)
 
let listSequence=0
const loadCompetitions = async () => {
  const sequence=++listSequence
  loading.value = true
  try {
    const token = getAuthToken()
    if (!token) {
      competitions.value = []
      return
    }
    const res = await axios.get('/api/teacher/competitions', {
      params: {
        status: activeTab.value === 'all' ? null : activeTab.value,
        search: searchQuery.value
      },
      headers: { Authorization: `Bearer ${token}` }
    })
    if(sequence!==listSequence)return
    competitions.value = (res.data && res.data.success && Array.isArray(res.data.data)) ? res.data.data : []
  } catch {
    if(sequence===listSequence)competitions.value = []
  } finally {
    if(sequence===listSequence)loading.value = false
  }
}
 
onMounted(async () => {
  await loadCompetitions()
})
 
let searchTimer
watch(activeTab, () => {clearTimeout(searchTimer);loadCompetitions()})
watch(searchQuery, () => {clearTimeout(searchTimer);searchTimer=setTimeout(loadCompetitions,300)})
onBeforeUnmount(()=>{clearTimeout(searchTimer);listSequence++})
 
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
}

const submissionsVisible = ref(false)
const submissionsLoading = ref(false)
const submissions = ref([])
const submissionScope=ref(route.query.review==='pending'?'pending':'all'),submissionQuery=ref(''),submissionError=ref('')
const pendingSubmissions=computed(()=>submissions.value.filter(isUngraded))
const visibleSubmissions=computed(()=>submissions.value.filter(row=>(submissionScope.value!=='pending' || isUngraded(row)) && `${row.userName} ${row.taskTitle}`.toLocaleLowerCase().includes(submissionQuery.value.trim().toLocaleLowerCase())))
const gradeVisible = ref(false)
const gradeSaving = ref(false)
const gradeTarget = ref(null)
const gradeScore = ref(0)
const gradeFeedback = ref('')
const nextUngraded=computed(()=>{
  const current=submissions.value.findIndex(row=>row.taskId===gradeTarget.value?.taskId && row.userId===gradeTarget.value?.userId)
  const ordered=[...submissions.value.slice(current+1),...submissions.value.slice(0,Math.max(0,current))]
  return ordered.find(isUngraded) || null
})
const gradeDirty=computed(()=>gradeTarget.value && (Number(gradeScore.value)!==Number(gradeTarget.value.score ?? 0) || gradeFeedback.value!==String(gradeTarget.value.feedback || '')))
async function canLeaveGrade(){
  if(gradeSaving.value){ElMessage.info('正在保存批改，请稍候');return false}
  if(gradeVisible.value && gradeDirty.value){try{await ElMessageBox.confirm('尚有未保存的分数或评语，确定离开当前批改？','保留本次修改？',{confirmButtonText:'放弃修改并返回',cancelButtonText:'继续批改',type:'warning'})}catch{return false}}
  return true
}
async function beforeGradeClose(done){if(await canLeaveGrade())done()}
onBeforeRouteLeave(canLeaveGrade)

const openSubmissions = async () => {
  if (!currentComp.value) return
  submissionQuery.value='';submissions.value=[]
  submissionsVisible.value = true
  await loadSubmissions()
}

const loadSubmissions = async () => {
  const compId = Number(currentComp.value?.id || 0)
  if (!compId) return
  const token = getAuthToken()
  if (!token) return
  if (submissionsLoading.value) return
  submissionsLoading.value = true
  submissionError.value=''
  try {
    const res = await axios.get(`/api/teacher/competitions/${compId}/submissions`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    submissions.value = (res.data && res.data.success && Array.isArray(res.data.submissions)) ? res.data.submissions : []
  } catch {
    submissionError.value='提交情况加载失败，请点击刷新重试'
    submissions.value = []
  } finally {
    submissionsLoading.value = false
  }
}

const openGrade = (row) => {
  if(!row?.submittedAt || gradeSaving.value)return
  gradeTarget.value = row || null
  gradeScore.value = Number(row?.score ?? 0)
  gradeFeedback.value = String(row?.feedback || '')
  gradeVisible.value = true
}

const saveGrade = async (moveNext=false) => {
  const row = gradeTarget.value
  if (!row) return
  const compId = Number(currentComp.value?.id || 0)
  if (!compId) return
  const token = getAuthToken()
  if (!token) return
  if (gradeSaving.value) return
  const score=Number(gradeScore.value),feedback=String(gradeFeedback.value || ''),next=nextUngraded.value
  if(!Number.isFinite(score) || score<0 || score>Number(row.points || 0)){ElMessage.warning('请输入有效分数');return}
  gradeSaving.value = true
  try {
    const res = await axios.post(
      `/api/teacher/competitions/${compId}/grade`,
      {
        task_id: String(row.taskId || ''),
        user_id: String(row.userId || ''),
        score,
        feedback
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    if (res.data && res.data.success) {
      ElMessage.success('已保存')
      const saved={...row,score:Number(res.data.score ?? score),feedback}
      submissions.value=submissions.value.map(item=>item.userId===row.userId && item.taskId===row.taskId?saved:item)
      gradeTarget.value=saved
      if(moveNext && next){gradeTarget.value=next;gradeScore.value=Number(next.score ?? 0);gradeFeedback.value=String(next.feedback || '')}
      else gradeVisible.value=false
    } else {
      ElMessage.error(res.data?.detail || res.data?.message || '保存失败')
    }
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    gradeSaving.value = false
  }
}

const endCompetition = async () => {
  const compId = Number(currentComp.value?.id || 0)
  if (!compId) return
  const token = getAuthToken()
  if (!token) return
  try {
    await ElMessageBox.confirm('确定要提前终止该测试吗？终止后学生将无法继续进入/提交。', '提示', {
      type: 'warning',
      confirmButtonText: '终止',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    const res = await axios.post(`/api/teacher/competitions/${compId}/end`, {}, { headers: { Authorization: `Bearer ${token}` } })
    if (res.data && res.data.success) {
      ElMessage.success('已终止')
      if (currentComp.value) currentComp.value.status = 'ended'
      await loadCompetitions()
    } else {
      ElMessage.error(res.data?.detail || res.data?.message || '终止失败')
    }
  } catch {
    ElMessage.error('终止失败')
  }
}
 
const publishVisible = ref(false)
const publishing = ref(false)
const tasksLoading = ref(false)
const teacherTasks = ref([])
const registerRange = ref([])
const competitionRange = ref([])
const usePointsRewards = ref(false)
const pointsRewards = ref({
  first: 200,
  second: 100,
  third: 50,
  participation: 0
})
const publishForm = ref({
  name: '',
  desc: '',
  type: 'algorithm',
  mode: 'general',
  status: 'registering',
  difficulty: '中等',
  duration: '4小时',
  register_time: '',
  competition_time: '',
  tags: '',
  task_ids: [],
  problems: [],
  detail_desc: '',
  rules: '',
  rewards: ''
})
 
const normalizeRangeStr = (r) => {
  const arr = Array.isArray(r) ? r : []
  const a = String(arr[0] || '').trim()
  const b = String(arr[1] || '').trim()
  if (!a || !b) return ''
  return `${a} ~ ${b}`
}

const openPublish = () => {
  publishForm.value = {
    name: '',
    desc: '',
    type: 'algorithm',
    mode: 'general',
    status: 'registering',
    difficulty: '中等',
    duration: '4小时',
    register_time: '',
    competition_time: '',
    tags: '',
    task_ids: [],
    problems: [],
    detail_desc: '',
    rules: '',
    rewards: ''
  }
  registerRange.value = []
  competitionRange.value = []
  usePointsRewards.value = false
  pointsRewards.value = { first: 200, second: 100, third: 50, participation: 0 }
  publishVisible.value = true
  loadTeacherTasks()
}

const loadTeacherTasks = async () => {
  const token = getAuthToken()
  if (!token) {
    teacherTasks.value = []
    return
  }
  if (tasksLoading.value) return
  tasksLoading.value = true
  try {
    const res = await fetch('/api/teacher/tasks', { headers: { Authorization: `Bearer ${token}` } })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      teacherTasks.value = []
      return
    }
    teacherTasks.value = Array.isArray(data?.tasks) ? data.tasks : []
  } catch {
    teacherTasks.value = []
  } finally {
    tasksLoading.value = false
  }
}

const syncProblemsFromSelected = () => {
  const selected = Array.isArray(publishForm.value.task_ids) ? publishForm.value.task_ids : []
  const prev = Array.isArray(publishForm.value.problems) ? publishForm.value.problems : []
  const prevMap = new Map(prev.map(p => [String(p.task_id), p]))
  const taskMap = new Map((teacherTasks.value || []).map(t => [String(t.id), t]))

  const next = []
  selected.forEach((tid, idx) => {
    const key = String(tid)
    const old = prevMap.get(key)
    const t = taskMap.get(key)
    next.push({
      task_id: key,
      title: String(t?.title || old?.title || key),
      category: String(old?.category || ''),
      points: Number(old?.points || 100),
      sort: idx
    })
  })
  publishForm.value.problems = next
}

watch(
  () => publishForm.value.task_ids,
  () => syncProblemsFromSelected(),
  { deep: true }
)

watch(
  registerRange,
  (v) => {
    publishForm.value.register_time = normalizeRangeStr(v)
  },
  { deep: true }
)

watch(
  competitionRange,
  (v) => {
    publishForm.value.competition_time = normalizeRangeStr(v)
  },
  { deep: true }
)

const buildPointsRewardsText = (r) => {
  const first = Number(r?.first || 0)
  const second = Number(r?.second || 0)
  const third = Number(r?.third || 0)
  const participation = Number(r?.participation || 0)
  const lines = []
  if (first > 0) lines.push(`一等奖：${first}积分`)
  if (second > 0) lines.push(`二等奖：${second}积分`)
  if (third > 0) lines.push(`三等奖：${third}积分`)
  if (participation > 0) lines.push(`参与奖：${participation}积分`)
  return lines.join('\n')
}

watch(
  [usePointsRewards, pointsRewards],
  () => {
    if (!usePointsRewards.value) return
    publishForm.value.rewards = buildPointsRewardsText(pointsRewards.value)
  },
  { deep: true }
)

const removeProblem = (taskId) => {
  const tid = String(taskId || '')
  publishForm.value.task_ids = (publishForm.value.task_ids || []).filter(x => String(x) !== tid)
  syncProblemsFromSelected()
}
 
const publish = async () => {
  const token = getAuthToken()
  if (!token) {
    ElMessage.error('请先登录')
    return
  }
  const payload = {
    name: String(publishForm.value.name || '').trim(),
    desc: String(publishForm.value.desc || '').trim(),
    type: String(publishForm.value.type || 'algorithm'),
    mode: String(publishForm.value.mode || 'general'),
    status: String(publishForm.value.status || 'registering'),
    difficulty: String(publishForm.value.difficulty || '中等'),
    duration: String(publishForm.value.duration || '4小时'),
    register_time: String(publishForm.value.register_time || '').trim(),
    competition_time: String(publishForm.value.competition_time || '').trim(),
    tags: String(publishForm.value.tags || '').trim(),
    problems: (publishForm.value.problems || []).map((p, idx) => ({
      task_id: String(p?.task_id || '').trim(),
      category: String(p?.category || '').trim(),
      points: Number(p?.points || 100),
      sort: Number.isFinite(Number(p?.sort)) ? Number(p.sort) : idx
    })),
    detail_desc: String(publishForm.value.detail_desc || '').trim(),
    rules: String(publishForm.value.rules || '').trim(),
    rewards: String(publishForm.value.rewards || '').trim()
  }
  if (!payload.name || !payload.desc) {
    ElMessage.warning('请填写名称与简介')
    return
  }
  if (payload.mode === 'problem_set' && (!payload.problems || payload.problems.length === 0)) {
    ElMessage.warning('做题测试需要添加题目')
    return
  }
  publishing.value = true
  try {
    const res = await fetch('/api/teacher/competitions/publish', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok || data?.success === false) {
      throw new Error(data?.detail || data?.message || '发布失败')
    }
    ElMessage.success('发布成功')
    publishVisible.value = false
    await loadCompetitions()
  } catch (e) {
    ElMessage.error(e?.message || '发布失败')
  } finally {
    publishing.value = false
  }
}
</script>
 
<style scoped>
.teacher-competition-page {
  min-height: calc(100vh - 60px);
  background: linear-gradient(135deg, #1f1538 0%, #2b1b4f 60%, #3a1c7a 100%);
  color: #fff;
  border-radius: 14px;
  overflow: hidden;
}
 
.hero-banner {
  padding: 48px 0 28px;
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
  font-size: 38px;
  font-weight: 900;
  margin: 0 0 12px;
}
 
.banner-subtitle {
  margin: 0 0 18px;
  color: rgba(255, 255, 255, 0.75);
}
 
.banner-stats {
  display: flex;
  gap: 18px;
}
 
.stat-item {
  background: rgba(255, 255, 255, 0.10);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 12px;
  padding: 12px 14px;
  min-width: 108px;
  text-align: center;
}
 
.stat-number {
  font-size: 22px;
  font-weight: 900;
  display: block;
}
 
.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}
 
.banner-right {
  display: flex;
  gap: 12px;
}
 
.feature-card {
  width: 120px;
  height: 96px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  display: grid;
  place-items: center;
}
 
.feature-icon {
  font-size: 26px;
}
 
.feature-text {
  font-weight: 800;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.88);
}
 
.filter-section {
  background: rgba(255, 255, 255, 0.04);
  border-top: 1px solid rgba(255, 255, 255, 0.10);
  border-bottom: 1px solid rgba(255, 255, 255, 0.10);
}
 
.filter-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
 
.filter-tabs {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
 
.tab-btn {
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.88);
  background: rgba(255, 255, 255, 0.06);
  border-radius: 999px;
  padding: 8px 12px;
  cursor: pointer;
}
 
.tab-btn.active {
  border-color: rgba(255, 255, 255, 0.55);
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  font-weight: 900;
}
 
.actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
 
.search-box {
  width: 260px;
}
 
.publish-btn {
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.35);
}
 
.competition-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 18px 24px 28px;
}
 
.loading-container {
  text-align: center;
  padding: 60px 0;
  color: rgba(255, 255, 255, 0.75);
}
 
.competition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
 
.competition-card {
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
 
.card-header {
  padding: 14px 14px 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
 
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 900;
}
 
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}
 
.dot.registering {
  background: #22c55e;
}
 
.dot.ongoing {
  background: #f59e0b;
}
 
.dot.ended {
  background: #a78bfa;
}
 
.competition-type {
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
}
 
.card-body {
  padding: 12px 14px 10px;
  flex: 1;
}
 
.competition-name {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 900;
  color: #fff;
}
 
.competition-desc {
  margin: 0 0 10px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  line-height: 1.5;
}
 
.info-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
 
.info-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
}
 
.time-info {
  display: grid;
  gap: 6px;
}
 
.time-item {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 12px;
}
 
.time-label {
  color: rgba(255, 255, 255, 0.65);
}
 
.card-footer {
  padding: 10px 14px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
 
.tag {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.88);
}
 
.footer-actions {
  display: flex;
  gap: 8px;
}

.empty-hint {
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
  padding: 6px 2px;
}
 
@media (max-width: 900px) {
  .banner-content {
    flex-direction: column;
    align-items: flex-start;
  }
  .actions {
    width: 100%;
    flex-wrap: wrap;
  }
  .search-box {
    width: 100%;
  }
}
</style>

<style scoped>
.pending-review-hint{max-width:1160px;margin:18px auto}.submission-tools{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:18px}.submission-tools .el-input{max-width:260px}.grade-heading{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:8px 0 24px}.grade-eyebrow{font:10px Consolas,monospace;letter-spacing:2px;color:#b59cc8}.grade-heading h2{font-size:22px;margin:12px 0 0;color:#4b315d}.grade-heading small{font-size:14px;color:#a18bb1;font-weight:400}.grade-layout{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:24px}.grade-reading{min-width:0}.grade-reading h3{font-size:13px;margin:0;color:#89729d}.grade-section-heading{display:flex;justify-content:space-between;align-items:center;padding:13px 16px;background:#eee7f6;border-radius:12px 12px 0 0}.grade-section-heading>span{font-size:11px;color:#aa93ba}.grade-code{font:13px/1.9 Consolas,monospace;margin:0;max-height:55vh;min-height:240px;overflow:auto;background:#21192e;color:#e4ddef;border-radius:0 0 12px 12px;padding:20px}.grade-output{margin-top:18px;border:1px solid #ece4f2;border-radius:12px;padding:16px}.grade-output pre{font:12px/1.8 Consolas,monospace;background:#f9f6fc;border-radius:8px;padding:12px;color:#816a92;max-height:180px;overflow:auto}.grade-error{color:#b5756f!important}.grade-assessment{position:sticky;top:0;align-self:start;padding:20px;border-radius:14px;background:#f8f4fc}.grade-max{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;color:#9f86b1;font-size:12px}.grade-max strong{font-size:28px;color:#8f6cab}.grade-max small{font-size:12px;font-weight:400}.grade-assessment .el-input-number{width:100%}.grade-next{font-size:12px;line-height:1.8;color:#9c84af;border-top:1px solid #e8dfef;padding-top:18px}.grade-next p{font-size:11px;color:#ad99bc;margin:8px 0 0}.grade-footer{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.grade-footer>span{flex:1}@media(max-width:760px){.grade-layout{grid-template-columns:1fr}.grade-assessment{position:static}.grade-heading{flex-wrap:wrap}.grade-footer>span{display:none}.grade-footer .el-button{margin:0}}
</style>

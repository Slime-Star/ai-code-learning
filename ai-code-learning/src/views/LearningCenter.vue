<template>
  <div class="learning-center">
    <!-- 移除无法使用的导航栏 -->

    <!-- 横幅区域 -->
    <section class="banner">
  <div class="banner-container">
    <div class="learning-entry-bar"><span><i aria-hidden="true"></i> 学习中心 · 从探索到实践</span><router-link to="/editor" class="coding-launch"><code aria-hidden="true">&gt;_</code><span>进入编程器<small>自由编写 · 运行代码 · AI 答疑</small></span><b aria-hidden="true">↗</b></router-link></div>
    <ContentBoundary silent><LearningHeroCarousel @browse="browseAllCourses" @path="selectPath(pathList.find(path => path.category === 'algorithm'))" /></ContentBoundary>

    <div class="continue-card">
      <div class="continue-copy">
        <span class="section-eyebrow">{{ lastCourse ? '接着上次，继续前进' : '你的学习，从这里开始' }}</span>
        <h2>{{ lastCourse ? lastCourse.name : '选一门课程，迈出第一步' }}</h2>
        <p>{{ lastCourse ? resumeDescription : '从感兴趣的方向开始，课程浏览记录会保存在当前浏览器。' }}</p>
        <div class="continue-actions">
          <el-button type="primary" :icon="VideoPlay" @click="lastCourse ? playCourse(lastCourse, $event) : browseCourses()">{{ lastCourse ? '继续学习' : '探索课程' }}</el-button>
          <el-button plain @click="showRecent">最近学习 · {{ recentCourses.length }}</el-button>
        </div>
      </div>
      <img v-if="lastCourse" :src="lastCourse.cover" :alt="lastCourse.name" class="continue-cover">
      <div v-else class="continue-symbol" aria-hidden="true">&lt;/&gt;</div>
    </div>

    <div class="banner-panels">
      <div class="banner-panel">
        <div class="panel-title-row">
          <div class="panel-title">近 {{ chartDays }} 天薄弱知识点</div>
          <div class="panel-actions">
            <el-button size="small" plain @click="refreshChart">刷新</el-button>
          </div>
        </div>
        <div class="panel-meta">
          <span class="meta-pill">总运行 {{ statsReady?statsSummary.totalRuns:'—' }} 次</span>
          <span class="meta-pill">错误 {{ statsReady?statsSummary.errorRuns:'—' }} 次</span>
          <span class="meta-pill">成功 {{ statsReady?statsSummary.successRuns:'—' }} 次</span>
        </div>
        <p v-if="chartStatsError" class="chart-stats-note">{{ chartStatsError }}</p><p v-else-if="sampledErrors!==null" class="chart-stats-note">错误主题基于本期最近 {{ sampledErrors }} 条失败提交，与右侧分析使用相同时间范围。</p>
        <div ref="chartRef" class="panel-chart"></div>
      </div>

      <div class="banner-panel analysis-panel"><LearningAnalysis @stats="syncAnalysisChart" @period="setAnalysisPeriod" /></div>
    </div>
  </div>
</section>

    <!-- 学习路径区域（修复点击事件） -->
    <section class="learning-path">
      <div class="path-container">
        <div class="path-header">
          <h2>📚 个性化学习路径</h2>
          <p>根据你的基础和目标，选择最适合的学习路线</p>
        </div>
        <ContentBoundary silent><KnowledgeMap :paths="pathList" :active-title="selectedPath" @select="path => selectPath(path, {scroll:false})" @browse="browseCourses" /></ContentBoundary>
        <div class="path-cards">
          <el-card v-for="(path, index) in pathList" :key="index" class="path-card" :class="{'path-selected':selectedPath === path.title}" shadow="hover">
            <span class="path-step" aria-hidden="true">{{ String(index + 1).padStart(2, '0') }} / PATH</span>
            <div class="path-icon">
              <el-icon :size="36" :color="path.color"><component :is="path.icon" /></el-icon>
            </div>
            <h3>{{ path.title }}</h3>
            <p class="path-desc">{{ path.desc }}</p>
            <div class="path-meta">
              <span>{{ path.courseCount }}门课程</span>
              <span>{{ path.hours }}小时</span>
              <span>{{ path.level }}</span>
            </div>
            <el-button type="primary" size="small" @click="selectPath(path)">开始学习</el-button>
          </el-card>
        </div>
      </div>
    </section>

    <!-- 课程分类区域 -->
    <div class="learning-interlude">
      <TopicArt scene="books" />
      <InlineTicTacToe />
    </div>
    <CodeTicker />
    <section id="course-catalog" class="course-category">
      <div class="category-container">
        <div class="category-header">
          <h2>🔧 课程分类</h2>
          <el-tabs v-model="activeCategory" class="category-tabs" @tab-change="clearPath">
            <el-tab-pane label="全部课程" name="all"></el-tab-pane>
            <el-tab-pane label="前端开发" name="frontend"></el-tab-pane>
            <el-tab-pane label="后端开发" name="backend"></el-tab-pane>
            <el-tab-pane label="移动开发" name="mobile"></el-tab-pane>
            <el-tab-pane label="人工智能" name="ai"></el-tab-pane>
            <el-tab-pane label="算法与数据结构" name="algorithm"></el-tab-pane>
            <el-tab-pane label="数据库" name="database"></el-tab-pane>
            <el-tab-pane label="开发工具" name="tools"></el-tab-pane>
          </el-tabs>
        </div>

        <div class="course-tools">
          <el-input v-model="searchQuery" placeholder="搜索课程、讲师或关键词" :prefix-icon="Search" clearable aria-label="搜索课程" />
          <el-select v-model="selectedLevel" aria-label="课程难度">
            <el-option label="全部难度" value="all" />
            <el-option v-for="level in courseLevels" :key="level" :label="level" :value="level" />
          </el-select>
        </div>
        <div class="course-scope" role="group" aria-label="课程范围">
          <button v-for="scope in courseScopes" :key="scope.value" :aria-pressed="courseScope === scope.value"
            :class="{ selected: courseScope === scope.value }" @click="courseScope = scope.value">{{ scope.label }}</button>
        </div>
        <div class="filter-summary" role="status" aria-live="polite" aria-atomic="true">
          <span>共 {{ filterCourses.length }} 门课程</span>
          <el-tag v-if="selectedPath" closable @close="clearPath">{{ selectedPath }}</el-tag>
          <el-button v-if="hasFilters" link type="primary" @click="resetFilters">清除筛选</el-button>
        </div>
        <div v-if="!filterCourses.length" class="course-empty">
          <el-empty :description="emptyDescription">
            <el-button v-if="courseScope === 'collected' && !isLogin" type="primary" @click="login">登录后查看收藏</el-button>
            <el-button v-else @click="resetFilters">浏览全部课程</el-button>
          </el-empty>
        </div>

        <!-- 课程列表 -->
        <TransitionGroup name="course" tag="div" class="course-list" @before-enter="prepareCourseCard" @before-leave="freezeCourseCard">
          <el-card v-for="(course, index) in paginatedCourses" :key="course.id" class="course-card" :data-motion-key="`course:${course.id}`" :style="{'--course-delay':`${Math.min(index * 35,210)}ms`}" shadow="hover">
            <div class="course-cover">
              <img
                :src="course.cover"
                :alt="course.name"
                :loading="index < 2 ? 'eager' : 'lazy'"
                decoding="async"
                @error="onCoverError"
              >
              <div class="course-duration">{{ course.duration }}</div>
              <div class="course-level" :style="{ backgroundColor: getLevelColor(course.level) }">{{ course.level }}</div>
              <button class="course-play-overlay" :aria-label="`${courseAction(course)} ${course.name}`" @click="playCourse(course, $event)"><span><el-icon><VideoPlay /></el-icon> {{ courseAction(course) }}</span></button>
            </div>
            <div class="course-info">
              <h3 class="course-title">{{ course.name }}</h3>
              <p class="course-desc" :title="course.desc">{{ course.desc }}</p>
              <div class="course-progress">
                <template v-if="courseRecords[String(course.id)]">
                  <div class="progress-caption"><span>{{ courseRecords[String(course.id)].percent === null ? '最近打开 · 随时继续' : courseRecords[String(course.id)].percent >= 98 ? '已完成 · 可再次回顾' : '已学 ' + courseRecords[String(course.id)].percent + '%' }}</span><span v-if="courseRecords[String(course.id)].position > 0">{{ formatStudyTime(courseRecords[String(course.id)].position) }}</span></div>
                  <div v-if="courseRecords[String(course.id)].percent !== null" class="course-progress-track" role="progressbar" :aria-label="`${course.name} 学习进度`" :aria-valuenow="courseRecords[String(course.id)].percent" aria-valuemin="0" aria-valuemax="100"><span :style="{width:courseRecords[String(course.id)].percent + '%'}"></span></div>
                </template>
                <span v-else class="progress-new">从这一课开始，积累一点新知识</span>
              </div>
              <div class="course-meta">
                <span><el-icon><User /></el-icon> {{ course.teacher }}</span>
                <span><el-icon><Star /></el-icon> {{ course.score }}</span>
                <span><el-icon><View /></el-icon> {{ course.viewCount }}人学习</span>
                <span><el-icon><Download /></el-icon> {{ course.downloadCount }}次下载</span>
              </div>
              <div class="course-tags">
                <el-tag v-for="tag in course.tags" :key="tag" size="small">{{ tag }}</el-tag>
              </div>
              <div class="course-actions">
                <el-button type="primary" size="small" :icon="VideoPlay" @click="playCourse(course, $event)">{{ courseAction(course) }}</el-button>
                <el-button 
                  size="small" 
                  :icon="Collection" 
                  :type="course.isCollected ? 'success' : 'default'"
                  :disabled="!isLogin"
                  :class="{ 'disabled-collect': !isLogin }"
                  :loading="collectingIds.has(String(course.id))"
                  @click="collectCourse(course)"
                >
                  <!-- 新增：根据登录状态显示不同文字 -->
                  {{ isLogin ? (course.isCollected ? '已收藏' : '收藏') : '请登录' }}
                </el-button>
                <el-button size="small" :icon="Share" @click="shareCourse(course)">分享</el-button>
              </div>
            </div>
          </el-card>
        </TransitionGroup>

        <!-- 分页控件 -->
        <div v-if="filterCourses.length" class="pagination">
          <el-pagination
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            :current-page="currentPage"
            :page-sizes="[6, 12, 18, 24]"
            :page-size="pageSize"
            layout="prev, pager, next"
            :pager-count="5"
            :total="filterCourses.length"
          >
          </el-pagination>
        </div>
      </div>
    </section>

    <StudyToolkit />
    <div class="learning-art-finale"><CodeLandscape variant="planet" /><TopicArt scene="launch" /></div>



    <CoursePlayer v-model:open="videoDialog" :course="currentCourse" :resume="currentResume" :origin="playbackOrigin" @progress="saveCourseProgress" />

    
  </div>
</template>

<script setup>
import defaultCourses from '@/config/courses.json'
import coursePlaceholder from '@/assets/course-placeholder.svg'
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import CoursePlayer from '@/components/CoursePlayer.vue'
import StudyToolkit from '@/components/StudyToolkit.vue'
import InlineTicTacToe from '@/components/InlineTicTacToe.vue'
import CodeTicker from '@/components/CodeTicker.vue'
import TopicArt from '@/components/TopicArt.vue'
import ContentBoundary from '@/components/ContentBoundary.vue'
import LearningHeroCarousel from '@/components/LearningHeroCarousel.vue'
import LearningAnalysis from '@/components/LearningAnalysis.vue'
import KnowledgeMap from '@/components/KnowledgeMap.vue'
import CodeLandscape from '@/components/CodeLandscape.vue'
import { normalizeCourses } from '@/utils/courseCatalog'
import { loadCourseCollections, setCourseCollected } from '@/utils/courseCollections'
import { useLearningHistory } from '@/composables/useLearningHistory'
import { useRouter } from 'vue-router'
import {
  ElMessage, ElMessageBox, ElEmpty, ElCard, ElButton, ElIcon,
  ElInput, ElTabs, ElTabPane, ElPagination, ElTag, ElProgress, ElDialog,
  ElTree
} from 'element-plus'
import {
  Document, House, VideoPlay, MapLocation, EditPen, User, Search, Collection,
  Share, Star, View, Download, Clock, Check, Message, 
  ChatDotRound, Setting, QuestionFilled, Comment
} from '@element-plus/icons-vue'
import { getAuthToken, getCurrentUser, removeAuthToken, removeCurrentUser, setCurrentUser } from '@/utils/authStorage'

const router = useRouter()

const chartRef = ref(null)
let chartInstance = null
let chartObserver = null
let chartResizeFrame = 0
// const getStatsStorageKey = () => {
//   const userRaw = localStorage.getItem('currentUser')
//   const user = userRaw ? JSON.parse(userRaw) : null
//   const userId = user?.id || 'guest'
//   return `codeRunStats_${userId}`
// }

// const loadRunStats = () => {
//   const raw = localStorage.getItem(getStatsStorageKey())
//   if (!raw) {
//     return { totalRuns: 0, successRuns: 0, errorRuns: 0, errors: {}, byLang: {}, lastRun: null }
//   }
//   try {
//     const parsed = JSON.parse(raw)
//     return {
//       totalRuns: parsed.totalRuns || 0,
//       successRuns: parsed.successRuns || 0,
//       errorRuns: parsed.errorRuns || 0,
//       errors: parsed.errors || {},
//       byLang: parsed.byLang || {},
//       lastRun: parsed.lastRun || null
//     }
//   } catch {
//     return { totalRuns: 0, successRuns: 0, errorRuns: 0, errors: {}, byLang: {}, lastRun: null }
//   }
// }
// ========== 新增：从数据库加载统计数据 ==========
// 获取当前登录用户ID
const getCurrentStudentId = () => {
  let studentId = 'guest';
  const user = getCurrentUser()
  if (user?.id) studentId = user.id
  if (studentId === 'guest') {
    studentId = localStorage.getItem('currentUserId') || 'guest';
  }
  return studentId;
};

// 从数据库加载知识点统计（用于饼状图）
const chartDays=ref(30),statsReady=ref(false),sampledErrors=ref(null),chartStatsError=ref('')
let statsController,statsSequence=0,statsActive=true
function syncAnalysisChart(stats){if(!statsActive)return;chartDays.value=stats.period.days;statsReady.value=true;sampledErrors.value=stats.sampledErrors;chartStatsError.value='';statsSummary.value={totalRuns:stats.totalRuns,successRuns:stats.successRuns,errorRuns:stats.errorRuns,errors:{}};updatePieChartWithKnowledge(stats.topics || [])}
function setAnalysisPeriod(days){chartDays.value=days;loadKnowledgeStats()}
const loadKnowledgeStats = async () => {
  statsController?.abort();statsController=new AbortController();const current=++statsSequence
  if(!getCurrentUser()?.id){statsReady.value=false;sampledErrors.value=null;chartStatsError.value='登录后查看学习统计';updatePieChartWithKnowledge([]);return}
  try{
    const response=await fetch('/api/learning-analysis',{method:'POST',signal:statsController.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({days:chartDays.value,mode:'quick'})})
    const data=await response.json().catch(()=>({}))
    if(!response.ok || !data.success || !data.stats)throw new Error(data.detail || '统计暂时无法加载，请刷新重试')
    if(statsActive && current===statsSequence)syncAnalysisChart(data.stats)
  }catch(error){if(statsActive && current===statsSequence && error.name!=='AbortError'){statsReady.value=false;sampledErrors.value=null;chartStatsError.value=error.message;updatePieChartWithKnowledge([])}}
}

// 用知识点数据更新饼状图
const updatePieChartWithKnowledge = (knowledgePoints) => {
  if (!chartRef.value) return;
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, null, {renderer:'svg'});
  }
  
  let data = [];
  if (knowledgePoints.length === 0) {
    data = [];
  } else {
    data = knowledgePoints.map(item => ({
      name: item.topic,
      value: item.count
    }));
  }

  const itemCount = data.length
  const compact = itemCount >= 6
  const panelWidth = Number(chartRef.value?.clientWidth || 0)
  const showLabels = !compact && itemCount <= 4 && panelWidth >= 520
  
  const option = {
    graphic: knowledgePoints.length?[]:[{id:'learning-empty',type:'text',left:'center',top:'42%',style:{text:statsReady.value?'本期暂无错误记录':'暂无统计数据',fill:'#e7ddf5',fontSize:13}}],
    tooltip: { 
      trigger: 'item',
      formatter: '{b}: {c} 次 ({d}%)'
    },
    legend: compact
      ? {
          type: 'scroll',
          orient: 'horizontal',
          bottom: 0,
          left: 0,
          width: '100%',
          pageButtonPosition: 'end',
          textStyle: { color: '#fff', fontSize: 12 },
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 10,
          formatter: (name) => (String(name).length > 10 ? `${String(name).slice(0, 10)}…` : String(name))
        }
      : {
          bottom: 0,
          left: 'center',
          textStyle: { color: '#fff', fontSize: 12 },
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 10,
          formatter: (name) => (String(name).length > 14 ? `${String(name).slice(0, 14)}…` : String(name))
        },
    series: [
      {
        name: '薄弱知识点',
        type: 'pie',
        radius: compact ? ['44%', '80%'] : ['44%', '78%'],
        center: compact ? ['50%', '44%'] : ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: 'rgba(255,255,255,0.25)', borderWidth: 1 },
        label: showLabels ? { color: '#fff', formatter: '{b}: {d}%' } : { show: false },
        emphasis: { label: { fontSize: 14, fontWeight: 'bold' } },
        labelLine: showLabels
          ? { lineStyle: { color: 'rgba(255,255,255,0.6)' }, length: 10, length2: 8 }
          : { show: false },
        labelLayout: { hideOverlap: true },
        data
      }
    ]
  };
  chartInstance.setOption(option, true);
};

// const statsSummary = ref(loadRunStats())替换为
const statsSummary = ref({ totalRuns: 0, successRuns: 0, errorRuns: 0, errors: {} });
const errorTypeLabel = (type) => {
  const map = {
    SyntaxError: '语法错误',
    IndentationError: '缩进错误',
    NameError: '名称未定义',
    ReferenceError: '引用未定义',
    TypeError: '类型错误',
    IndexError: '越界错误',
    NullPointerException: '空指针异常',
    CompilationError: '编译错误',
    ModuleNotFoundError: '模块未找到',
    Timeout: '超时',
    RuntimeError: '运行错误',
    Unknown: '未知错误'
  }
  return map[type] || String(type || '未知错误')
}

// const buildPieData = (stats) => {
//   const errors = stats?.errors || {}
//   const entries = Object.entries(errors).filter(([, v]) => Number(v) > 0)
//   if (entries.length === 0) {
//     return [{ name: '暂无错误', value: 1 }]
//   }
//   return entries.map(([k, v]) => ({ name: errorTypeLabel(k), value: v }))
// }

const renderChart = () => {
  statsSummary.value = loadRunStats()
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, null, {renderer:'svg'})
  }
  const data = buildPieData(statsSummary.value)
  const option = {
    tooltip: { trigger: 'item' },
    legend: {
      top: 'bottom',
      left: 'center',
      textStyle: { color: '#fff' }
    },
    series: [
      {
        name: '错误类型',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: 'rgba(255,255,255,0.25)', borderWidth: 1 },
        label: { color: '#fff' },
        emphasis: { label: { fontSize: 14, fontWeight: 'bold' } },
        labelLine: { lineStyle: { color: 'rgba(255,255,255,0.6)' } },
        data
      }
    ]
  }
  chartInstance.setOption(option)
  chartInstance.resize()
}

const refreshChart = async () => {
  // await nextTick()
  // renderChart()替换为
  await loadKnowledgeStats();
}

// ========== 新增：用户登录状态管理 ==========


// 当前登录用户（从本地存储读取，初始为null）
const userInfo = ref(getCurrentUser())
// 计算属性：判断是否登录
const isLogin = computed(() => !!userInfo.value)

// 模拟登录方法（实际项目替换为后端接口请求）
const login = () => {
  router.push('/login')
}

// 退出登录方法
const logout = () => {
  // 清空当前用户信息
  userInfo.value = null
  removeCurrentUser()
  removeAuthToken()
  // 重置课程收藏状态（界面上取消所有「已收藏」显示）
  courseList.value.forEach(course => course.isCollected = false)
  ElMessage.info('已退出登录')
}

// 同步用户收藏到课程列表（核心：让登录后课程的收藏状态和用户数据一致）
const syncUserCollections = () => {
  if (!isLogin.value) return // 未登录则不执行
  const userCollections = userInfo.value.collectedCourses || []
  // 遍历所有课程，匹配收藏状态
  courseList.value.forEach(course => {
    course.isCollected = userCollections.some(id => String(id) === String(course.id))
  })
}

// 分类激活项
const activeCategory = ref('all')
watch(activeCategory, () => {
  currentPage.value = 1
})
// 分页相关
const currentPage = ref(1)
const pageSize = ref(6)
// 视频弹窗
const videoDialog = ref(false)
const currentCourse = ref(null)
let playbackOwner = null
const { history, save: saveHistory } = useLearningHistory()
const searchQuery = ref('')
const selectedLevel = ref('all')
const courseScope = ref('all')
const selectedPath = ref('')
const courseScopes = [
  { label: '全部课程', value: 'all' },
  { label: '我的收藏', value: 'collected' },
  { label: '最近学习', value: 'recent' }
]
watch([searchQuery, selectedLevel, courseScope], () => { currentPage.value = 1 })
// 树形结构配置
const treeProps = ref({
  label: 'name',
  children: 'children'
})

// 学习路径数据
const pathList = ref([
  {
    id: 1,
    title: '前端开发工程师',
    desc: '从HTML/CSS/JS到Vue/React，掌握现代前端开发技能',
    icon: 'Document',
    color: '#409eff',
    courseCount: 28,
    hours: 320,
    level: '入门到进阶',
    category: 'frontend',
    keywords: ['HTML', 'CSS', 'JavaScript', 'Vue', 'React', '前端']
  },
  {
    id: 2,
    title: 'Python全栈开发',
    desc: 'Python基础+Web开发+数据分析+人工智能，全方向覆盖',
    icon: 'EditPen',
    color: '#67c23a',
    courseCount: 35,
    hours: 450,
    level: '全阶段',
    category: 'backend',
    keywords: ['Python', 'Django', 'Flask', '数据分析', 'AI']
  },
  {
    id: 3,
    title: 'Java后端开发',
    desc: 'Java基础+Spring全家桶+微服务，打造企业级后端架构',
    icon: 'Setting',
    color: '#e6a23c',
    courseCount: 42,
    hours: 500,
    level: '进阶到高级',
    category: 'backend',
    keywords: ['Java', 'Spring', 'MyBatis', '微服务', '后端']
  },
  {
    id: 4,
    title: '算法与数据结构',
    desc: '从基础算法到高级数据结构，攻克大厂面试难题',
    icon: 'Star',
    color: '#f56c6c',
    courseCount: 18,
    hours: 200,
    level: '全阶段',
    category: 'algorithm',
    keywords: ['算法', '数据结构', 'LeetCode', '面试']
  }
])
const selectedPathKeywords = ref([])

// 课程数据
const courseList = ref(normalizeCourses(defaultCourses))
async function loadCourseCatalog() {
  try {
    const res = await fetch('/api/catalog/courses', {cache:'no-store'})
    const data = await res.json()
    if (!res.ok || !Array.isArray(data.items)) throw new Error()
    courseList.value = normalizeCourses(data.items)
    syncUserCollections()
  } catch { ElMessage.warning('课程数据暂时无法同步，正在显示本地课程') }
}


// 热门课程（学习进度已修正为真实合理值）
const hotCourses = computed(() => {
  return [...courseList.value].sort((a, b) => b.viewCount - a.viewCount).slice(0, 6)
})

const courseLevels = computed(() => [...new Set(courseList.value.map(course => course.level))])
const recentCourses = computed(() => history.value.map(record => courseList.value.find(course => course.id === record.id)).filter(Boolean))
const lastCourse = computed(() => recentCourses.value[0] || null)
const currentResume = computed(() => history.value.find(record => record.id === currentCourse.value?.id) || null)
const courseRecords=computed(()=>Object.fromEntries(history.value.map(record=>[String(record.id),{
  position:record.position || 0,
  percent:Number.isFinite(record.position) && Number.isFinite(record.duration) && record.duration>0 ? Math.min(100,Math.max(0,Math.round(record.position/record.duration*100))) : null
}])))
function courseAction(course){
  const record=courseRecords.value[String(course.id)]
  return record?.percent>=98 ? '再次学习' : record ? '继续学习' : '开始学习'
}
function formatStudyTime(seconds){return `${Math.floor(seconds/60)}:${String(Math.floor(seconds%60)).padStart(2,'0')}`}
function onCoverError(event){
  const image=event.target
  if(image.dataset.fallback)return
  image.dataset.fallback='true'
  image.src=coursePlaceholder
}
const resumeDescription = computed(() => {
  const record = history.value.find(item => item.id === lastCourse.value?.id)
  if (record?.duration > 0 && record.position < record.duration - 2) {
    return `上次学到 ${Math.floor(record.position / 60)} 分 ${Math.floor(record.position % 60)} 秒，继续积累一点进步。`
  }
  return '上次打开的课程，点击即可再次观看。'
})
const hasFilters = computed(() => searchQuery.value.trim() || selectedLevel.value !== 'all' || courseScope.value !== 'all' || activeCategory.value !== 'all' || selectedPath.value)
const emptyDescription = computed(() => {
  if (courseScope.value === 'collected' && !isLogin.value) return '登录后，即可查看你收藏的课程'
  if (courseScope.value === 'recent' && !recentCourses.value.length) return '还没有学习记录，先选一门课程吧'
  if (courseScope.value === 'collected' && !courseList.value.some(course => course.isCollected)) return '还没有收藏课程，点击课程卡片上的收藏即可添加'
  return '没有找到符合条件的课程，试试其他关键词或清除筛选'
})
function clearPath() {
  selectedPath.value = ''
  selectedPathKeywords.value = []
  currentPage.value = 1
}
function resetFilters() {
  searchQuery.value = ''
  selectedLevel.value = 'all'
  courseScope.value = 'all'
  activeCategory.value = 'all'
  clearPath()
}
function browseCourses() {
  document.getElementById('course-catalog')?.scrollIntoView({
    behavior: 'smooth', block: 'start'
  })
}
async function browseAllCourses() {
  resetFilters()
  await nextTick()
  browseCourses()
}
function showRecent() {
  resetFilters()
  courseScope.value = 'recent'
  browseCourses()
}
function saveCourseProgress(progress) {
  if (currentCourse.value && playbackOwner === (getCurrentUser()?.id ?? 'guest')) saveHistory(currentCourse.value.id, progress)
}

// 筛选后的课程
const filterCourses = computed(() => {
  let filtered = courseScope.value === 'recent' ? [...recentCourses.value] : [...courseList.value]
  if (courseScope.value === 'collected') filtered = filtered.filter(course => isLogin.value && course.isCollected)
  const query = searchQuery.value.trim().toLocaleLowerCase()
  if (query) filtered = filtered.filter(course =>
    `${course.name} ${course.desc} ${course.teacher} ${(course.tags || []).join(' ')}`.toLocaleLowerCase().includes(query)
  )
  if (selectedLevel.value !== 'all') filtered = filtered.filter(course => course.level === selectedLevel.value)

  // 如果有路径关键词，优先按关键词筛选
  if (selectedPathKeywords.value.length > 0) {
    filtered = filtered.filter(course => {
      const courseText = `${course.name} ${course.desc} ${(course.tags || []).join(' ')}`
      return selectedPathKeywords.value.some(keyword => courseText.includes(keyword))
    })
  } else {
    // 没有路径关键词时，只按分类筛选
    if (activeCategory.value !== 'all') {
      filtered = filtered.filter(course => course.category === activeCategory.value)
    }
  }

  return filtered
})

// 分页后的课程
const paginatedCourses = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filterCourses.value.slice(start, end)
})
watch(() => filterCourses.value.length, length => {
  currentPage.value = Math.min(currentPage.value, Math.max(1, Math.ceil(length / pageSize.value)))
})

// 获取难度等级颜色
const getLevelColor = (level) => {
  switch(level) {
    case '入门': return '#67c23a'
    case '中级': return '#409eff'
    case '高级': return '#f56c6c'
    default: return '#909399'
  }
}

// 方法：选择学习路径（修复点击事件，添加跳转逻辑）
const selectPath = async (path, options = {}) => {
  resetFilters()
  await nextTick()
  selectedPath.value = path.title
  selectedPathKeywords.value = path.keywords || []
  currentPage.value = 1
  if(options.scroll !== false)browseCourses()
  ElMessage.success(`已为你选择【${path.title}】学习路径，正在展示相关课程`)
}

// 方法：播放课程
function prepareCourseCard(element){element.style.width=''}
function freezeCourseCard(element){element.style.width=`${element.getBoundingClientRect().width}px`}
const playbackOrigin = ref(null)
const playCourse = (course, event) => {
  playbackOrigin.value = event?.currentTarget?.closest('.continue-card')?.querySelector('.continue-cover') || event?.currentTarget?.closest('.course-card')?.querySelector('.course-cover') || Array.from(document.querySelectorAll('[data-motion-key]')).find(node=>node.dataset.motionKey===`course:${course.id}`)?.querySelector('.course-cover') || event?.currentTarget

  playbackOwner = getCurrentUser()?.id ?? 'guest'
  saveHistory(course.id)
  currentCourse.value = course
  videoDialog.value = true
}
// 收藏课程（带权限控制 + 持久化）
const collectingIds = ref(new Set())
const collectCourse = async (course) => {
  if (!isLogin.value) {
    try {
      await ElMessageBox.confirm('收藏课程需要先登录，是否立即登录？', '操作提示', {confirmButtonText:'立即登录',cancelButtonText:'取消',type:'info'})
      login()
    } catch { /* The user chose to keep browsing. */ }
    return
  }
  const key = String(course.id)
  if (collectingIds.value.has(key)) return
  collectingIds.value.add(key)
  const collected = !course.isCollected
  try {
    await setCourseCollected(course.id, collected)
    ElMessage.success(collected ? `已收藏【${course.name}】，可在个人中心查看` : `已取消收藏【${course.name}】课程`)
  } catch (error) { ElMessage.error(error.message || '收藏保存失败，请重试') }
  finally { collectingIds.value.delete(key) }
}

function syncCollectionChanges() {
  userInfo.value = getCurrentUser()
  syncUserCollections()
}
async function refreshCollections() {
  if (!getCurrentUser()?.id) return
  try {
    const data = await loadCourseCollections()
    if (data) syncCollectionChanges()
  } catch (error) { ElMessage.warning(error.message || '收藏暂时无法同步，请稍后重试') }
}

// 方法：分享课程
const shareCourse = async (course) => {
  try {
    await navigator.clipboard.writeText(course.videoUrl)
    ElMessage.success(`已复制【${course.name}】课程链接到剪贴板`)
  } catch {
    ElMessage.warning('复制失败，请检查浏览器剪贴板权限')
  }
}

// 方法：选择章节
const selectChapter = (data) => {
  ElMessage.info(`选择了章节：${data.name}`)
}

// 方法：查看更多热门课程
const seeMoreHot = () => {
  activeCategory.value = 'all'
  currentPage.value = 1
  ElMessage.info('已切换到全部课程列表')
}

// 方法：前往课程中心
const goToCourse = () => {
  activeCategory.value = 'all'
  currentPage.value = 1
  ElMessage.info('欢迎来到课程中心')
}

// 分页方法
const handleSizeChange = (val) => {
  pageSize.value = val
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// ========== 修改：页面加载时同步收藏状态 ==========
function syncLearningUser() {
  userInfo.value = getCurrentUser()
  loadKnowledgeStats()
  courseList.value.forEach(course => { course.isCollected = false })
  syncUserCollections()
  videoDialog.value = false
}

onMounted(() => {
  loadCourseCatalog()
  window.addEventListener('user-updated', syncLearningUser)
  if (chartRef.value) {
    chartObserver = new ResizeObserver(() => {
      cancelAnimationFrame(chartResizeFrame)
      chartResizeFrame = requestAnimationFrame(() => chartInstance?.resize())
    })
    chartObserver.observe(chartRef.value)
  }
  refreshCollections()
  window.addEventListener('course-collections-updated', syncCollectionChanges)
  window.addEventListener('focus', refreshCollections)
  syncUserCollections() // 新增：登录状态下同步收藏列表 
  loadKnowledgeStats();  // 改为从数据库加载
  window.addEventListener('code-run-stats-updated', refreshChart)
})

onUnmounted(() => {
  statsActive=false;statsSequence++;statsController?.abort()
  chartObserver?.disconnect()
  cancelAnimationFrame(chartResizeFrame)
  window.removeEventListener('user-updated', syncLearningUser)
  window.removeEventListener('course-collections-updated', syncCollectionChanges)
  window.removeEventListener('focus', refreshCollections)
  window.removeEventListener('code-run-stats-updated', refreshChart)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

</script>

<style scoped>
.learning-art-finale { max-width: 1280px; margin: 0 auto; padding: 8px 20px; display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr); align-items: center; }
@media (max-width: 768px) { .learning-art-finale { grid-template-columns: minmax(0,1fr); }.learning-art-finale :deep(.topic-art) { display: none; } }
.learning-interlude { max-width: 1400px; margin: 0 auto; padding: 12px 40px 12px 20px; display: grid; grid-template-columns: minmax(0,1fr) auto; align-items: center; gap: 24px; }
.learning-interlude :deep(.topic-art) { width: 100%; margin: 0; }
@media (max-width: 768px) { .learning-interlude { padding: 24px 20px; grid-template-columns: minmax(0,1fr); justify-items: center; }.learning-interlude :deep(.topic-art) { display: none; } }
.banner-top { position: relative; isolation: isolate; }
.banner-top h1, .banner-top > p { position: relative; z-index: 1; }
.path-header { position: relative; }
.learning-shortcuts { position: relative; z-index: 1; display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
.learning-shortcuts a, .learning-shortcuts button { display: inline-flex; align-items: center; gap: 9px; min-height: 40px; padding: 9px 14px; border: 1px solid #ffffff45; border-radius: 9px; background: #ffffff12; color: #fff; text-decoration: none; font: inherit; font-size: 12px; cursor: pointer; transition: background-color 180ms, transform 180ms; }
.learning-shortcuts a:hover, .learning-shortcuts button:hover { background: #ffffff24; transform: translateY(-2px); }
.learning-shortcuts a:active, .learning-shortcuts button:active { transform: translateY(0); }
.path-card { position: relative; }
.path-step { display: block; text-align: right; font: 10px Consolas, monospace; letter-spacing: 1px; color: #8b83a6; margin-bottom: 4px; }
.path-card:focus-within { outline: 2px solid #b5a1ea; outline-offset: 2px; }
.course-play-overlay { position: absolute; inset: 0; display: grid; place-items: center; border: 0; background: #2e225640; cursor: pointer; opacity: 0; transition: opacity 200ms; color: #fff; }
.course-play-overlay > span { display: inline-flex; align-items: center; gap: 8px; padding: 11px 16px; border: 1px solid #ffffff70; border-radius: 24px; background: #322454c9; font-size: 12px; transform: translateY(8px); transition: transform 200ms; }
.course-play-overlay .el-icon { font-size: 21px; }
.course-cover:hover .course-play-overlay, .course-play-overlay:focus-visible { opacity: 1; }
.course-cover:hover .course-play-overlay > span, .course-play-overlay:focus-visible > span { transform: translateY(0); }
.course-play-overlay:focus-visible { outline: 3px solid #c4b5fd; outline-offset: -4px; }
@media (hover: none) { .course-play-overlay { opacity: 1; background: transparent; place-items: end center; padding-bottom: 12px; } .course-play-overlay > span { padding: 6px 12px; transform: none; } }
@media (max-width: 768px) { .learning-shortcuts { justify-content: center; gap: 8px; } .learning-shortcuts a, .learning-shortcuts button { padding: 8px 10px; font-size: 11px; } }
.course-enter-active, .course-leave-active, .course-move {
  transition: opacity 220ms ease, transform 220ms ease;
}
.course-enter-from, .course-leave-to { opacity: 0; transform: translateY(14px); }
.course-leave-active { position: absolute; pointer-events: none; }
.course-list { position: relative; }
.path-card, .course-card { transition: transform 220ms ease, box-shadow 220ms ease; }
@media (hover: hover) {
  .path-card:hover, .course-card:hover { transform: translateY(-5px); }
}

:global(.toast-noclick) {
  pointer-events: none;
}

:global(.toast-bottomright) {
  left: auto !important;
  right: 16px !important;
  top: auto !important;
  bottom: 16px !important;
  transform: none !important;
  max-width: 260px;
}

/* 全局样式 */
.learning-center {
  width: 100%;
  min-height: 100vh;
  background-color: #f5f7fa;
  font-family: "Microsoft YaHei", sans-serif;
}

/* 横幅区域 */
.banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 60px 0;
}

.banner-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  padding: 0 20px;
  gap: 18px;
}

.banner-top {}

.banner-top h1 {
  font-size: 42px;
  margin-bottom: 20px;
  line-height: 1.4;
}

.banner-top p {
  font-size: 18px;
  margin-bottom: 30px;
  color: #e0e0e0;
}

.banner-panels {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.banner-panel {
  width: 100%;
  height: 380px;
  padding: 14px 14px 10px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 12px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.panel-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 12px;
  color: #fff;
}

.panel-chart {
  width: 100%;
  height: 300px;
  margin-top: 8px;
}

.panel-analysis {
  margin-top: 10px;
  flex: 1;
  background: rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  padding: 10px 12px;
  overflow: auto;
}

.analysis-provider {
  margin-top: 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.82);
}

.analysis-text {
  white-space: pre-wrap;
  line-height: 1.7;
  color: #fff;
  font-size: 13px;
}

@media (max-width: 1024px) {
  .banner-panels {
    grid-template-columns: 1fr;
  }
  .banner-panel {
    height: 340px;
  }
  .panel-chart {
    height: 240px;
  }
}

/* 学习路径 */
.learning-path {
  padding: 80px 0;
  background-color: #fff;
}

.path-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.path-header {
  text-align: center;
  margin-bottom: 40px;
}

.path-header h2 {
  font-size: 32px;
  color: #333;
  margin-bottom: 10px;
}

.path-header p {
  font-size: 16px;
  color: #666;
}

.path-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.path-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.path-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.path-icon {
  text-align: center;
  padding: 20px 0;
  border-bottom: 1px solid #f5f5f5;
}

.path-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 20px 20px 10px;
  color: #333;
}

.path-desc {
  font-size: 14px;
  color: #666;
  margin: 0 20px 20px;
  line-height: 1.6;
}

.path-meta {
  display: flex;
  gap: 15px;
  margin: 0 20px 20px;
  font-size: 12px;
  color: #999;
}

.path-card .el-button {
  margin: 0 20px 20px;
  width: calc(100% - 40px);
}

/* 课程分类 */
.course-category {
  padding: 80px 0;
  background-color: #f9f9f9;
}

.category-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.category-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.category-header h2 {
  font-size: 32px;
  color: #333;
  margin: 0;
}

.category-tabs {
  width: 70%;
}

/* 课程列表 */
.course-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.disabled-collect {
  cursor: not-allowed !important;
  opacity: 0.6;
}

.course-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.course-cover {
  position: relative;
  height: 180px;
  overflow: hidden;
}

.course-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.course-card:hover .course-cover img {
  transform: scale(1.05);
}

.course-duration {
  position: absolute;
  bottom: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.course-level {
  position: absolute;
  top: 10px;
  left: 10px;
  color: #fff;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.course-info {
  padding: 20px;
}

.course-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
  font-size: 12px;
  color: #999;
}

.course-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.course-actions {
  display: flex;
  gap: 10px;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 40px;
}

/* 热门推荐 */
.hot-recommend {
  padding: 80px 0;
  background-color: #fff;
}

.recommend-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.recommend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.recommend-header h2 {
  font-size: 32px;
  color: #333;
  margin: 0;
}

.hot-courses {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.hot-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
}

.hot-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.hot-cover {
  position: relative;
  height: 140px;
  overflow: hidden;
}

.hot-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hot-rank {
  position: absolute;
  top: 0;
  left: 0;
  width: 30px;
  height: 30px;
  background-color: #f56c6c;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  border-radius: 0 0 12px 0;
}

.hot-info {
  padding: 15px;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.hot-info h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hot-info p {
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
}

.hot-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: auto;
}

.hot-progress .el-progress {
  flex: 1;
}

.hot-progress span {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

/* 视频播放弹窗 */
.video-player-container {
  display: flex;
  gap: 20px;
  height: 600px;
}

.player-wrapper {
  flex: 3;
}

.player-sidebar {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.player-chapters {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 15px;
  flex: 2;
  overflow-y: auto;
}

.player-chapters h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #333;
}

.player-info {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 15px;
  flex: 1;
}

.player-info h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #333;
}

.player-info p {
  font-size: 14px;
  color: #666;
  margin-bottom: 15px;
  line-height: 1.6;
}

.player-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
  font-size: 12px;
  color: #999;
}

.empty-player {
  padding: 40px;
  text-align: center;
}

/* 页脚 */
.learning-footer {
  background-color: #2c3e50;
  color: #fff;
  padding: 60px 0 20px;
}

.footer-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 40px;
  margin-bottom: 40px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 40px;
}

.link-group h3 {
  font-size: 18px;
  margin-bottom: 20px;
  position: relative;
  padding-bottom: 10px;
}

.link-group h3::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 40px;
  height: 2px;
  background-color: #409eff;
}

.link-group ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.link-group li {
  margin-bottom: 10px;
}

.link-group a {
  color: #b0b0b0;
  text-decoration: none;
  transition: color 0.3s ease;
}

.link-group a:hover {
  color: #409eff;
}

.social-links {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.social-icon {
  cursor: pointer;
  transition: color 0.3s ease;
}

.social-icon:hover {
  color: #409eff;
}

.contact, .email {
  font-size: 14px;
  color: #b0b0b0;
  margin-bottom: 10px;
}

.footer-copyright {
  text-align: center;
  font-size: 14px;
  color: #999;
  line-height: 1.6;
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .banner-container {
    flex-direction: column;
    text-align: center;
  }
  
  .banner-content h1 {
    font-size: 32px;
  }
  
  .category-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  
  .category-tabs {
    width: 100%;
  }
  
  .video-player-container {
    flex-direction: column;
    height: auto;
  }
  
  .player-wrapper {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .banner {
    padding: 40px 0;
  }
  
  .banner-content h1 {
    font-size: 24px;
  }
  
  .path-header h2, .category-header h2, .recommend-header h2 {
    font-size: 24px;
  }
  
  .learning-path, .course-category, .hot-recommend {
    padding: 40px 0;
  }
  
  .player-wrapper {
    height: 300px;
  }
  
  .footer-links {
    gap: 20px;
  }
}
.continue-card {
  display: flex; justify-content: space-between; align-items: center; gap: 24px;
  padding: 28px; border-radius: 20px; color: #fff;
  background: rgba(40, 33, 97, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: 0 10px 28px rgba(33, 24, 85, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px); text-align: left;
}
.continue-copy { min-width: 0; }
.section-eyebrow { color: #eef2ff; font-size: 13px; font-weight: 600; }
.continue-card h2 { font-size: 25px; line-height: 1.5; margin: 8px 0; }
.continue-card p { color: #f0f2ff; line-height: 1.8; font-size: 14px; }
.continue-actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 20px; }
.continue-actions .el-button + .el-button { margin-left: 0; }
.continue-actions .el-button.is-plain {
  --el-button-bg-color: rgba(255, 255, 255, 0.08);
  --el-button-border-color: rgba(255, 255, 255, 0.32);
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: rgba(255, 255, 255, 0.16);
  --el-button-hover-border-color: rgba(255, 255, 255, 0.55);
  --el-button-hover-text-color: #fff;
  --el-button-active-bg-color: rgba(255, 255, 255, 0.2);
  --el-button-active-border-color: rgba(255, 255, 255, 0.65);
  --el-button-active-text-color: #fff;
}
.continue-cover { width: 200px; height: 124px; object-fit: cover; border-radius: 12px; }
.continue-symbol { font-size: 54px; font-weight: bold; color: rgba(224, 231, 255, 0.45); padding: 0 30px; }
#course-catalog { scroll-margin-top: 80px; }
.course-tools { display: flex; gap: 14px; margin-bottom: 20px; }
.course-tools .el-input { max-width: 520px; }
.course-tools .el-select { width: 160px; flex-shrink: 0; }
.course-scope { display: flex; gap: 8px; flex-wrap: wrap; }
.course-scope button {
  font: inherit; font-size: 14px; padding: 9px 18px; border-radius: 20px;
  border: 1px solid #dce3ee; background: #fff; color: #475569; cursor: pointer;
  transition: background-color 180ms, color 180ms, border-color 180ms;
}
.course-scope button.selected { background: #eef2ff; color: #4f46e5; border-color: #a5b4fc; }
.filter-summary { min-height: 52px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; font-size: 13px; color: #64748b; }
.course-empty { background: #fff; border-radius: 16px; }
.banner-panel, .category-container, .path-container { min-width: 0; }
.course-list { grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr)); }
.path-cards { grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr)); }
@media (max-width: 640px) {
  .banner { padding: 28px 0; }
  .banner-top h1 { font-size: 28px; margin-bottom: 10px; }
  .banner-top p { font-size: 14px; margin-bottom: 8px; line-height: 1.8; }
  .continue-card { padding: 22px; }
  .continue-card h2 { font-size: 21px; }
  .continue-cover, .continue-symbol { display: none; }
  .course-tools { flex-direction: column; }
  .course-tools .el-input, .course-tools .el-select { width: 100%; max-width: none; }
  .course-actions { display: flex; flex-wrap: wrap; gap: 8px; }
  .course-actions .el-button + .el-button { margin-left: 0; }
  .path-header p { font-size: 14px; line-height: 1.8; }
}
.course-progress { min-height: 42px; margin: 12px 0 14px; }
.progress-caption { display: flex; justify-content: space-between; gap: 12px; font-size: 12px; color: #86709e; margin-bottom: 8px; }
.progress-new { display: block; padding-top: 5px; color: #a498b0; font-size: 12px; }
.course-progress-track { height: 5px; overflow: hidden; border-radius: 6px; background: #eee7f5; }
.course-progress-track > span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg,#9290e0,#bc95d4); transition: width 500ms cubic-bezier(.2,.75,.25,1); }
.course-card:focus-within .course-play-overlay { opacity: 1; }
.course-card:focus-within .course-play-overlay > span { transform: translateY(0); }
.course-card:focus-within { outline: 2px solid #baa1dc; outline-offset: 3px; }
.course-card .el-button--success { animation: collection-confirm 350ms ease-out; }
@keyframes collection-confirm { 50% { transform: scale(1.06); } }
@media(max-width:640px) { .course-progress { min-height: 38px; }.course-info { padding: 16px; }.course-meta { flex-wrap: wrap; row-gap: 8px; } }
.banner-top { display: grid; grid-template-columns: minmax(0,1fr) minmax(320px,450px); align-items: center; gap: 30px; min-height: 290px; }
.banner-copy { position: relative; z-index: 1; min-width: 0; }
.learning-hero-scene { justify-self: end; }
.path-header { margin-bottom: 26px; }
.path-card.path-selected { box-shadow: 0 0 0 2px #bea2d4, 0 8px 24px #9c7ab321; }
@media(max-width:1100px){.banner-top{grid-template-columns:minmax(0,1fr) 370px;gap:16px}.banner-top h1{font-size:34px}.banner-top p{font-size:15px;line-height:1.8}}
@media(max-width:850px){.banner-top{grid-template-columns:minmax(0,1fr);gap:4px;min-height:0}.learning-hero-scene{justify-self:center}.banner-copy{text-align:center}.learning-shortcuts{justify-content:center}}
@media(max-width:640px){.banner-top h1{font-size:28px}.banner-top p{font-size:14px;margin-bottom:20px}.learning-hero-scene{margin-top:4px}}
.learning-entry-bar{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:10px}.learning-entry-bar>span{font-size:12px;color:#eee2ffba;display:flex;align-items:center;gap:9px}.learning-entry-bar>span>i{width:5px;height:5px;border-radius:50%;background:#d1d9ff;box-shadow:0 0 0 4px #e7dbff15}.coding-launch{display:flex;align-items:center;gap:15px;min-width:290px;padding:12px 18px;border:1px solid #f4e7ffa0;border-radius:14px;background:linear-gradient(120deg,#fbf5ff,#e5e4ff);box-shadow:0 7px 25px #3a225c33;color:#76519a;text-decoration:none;transition:transform 220ms,box-shadow 220ms}.coding-launch code{display:grid;place-items:center;font:23px Consolas,monospace;width:42px;height:42px;border-radius:10px;background:#cdb7e838}.coding-launch>span{font-size:16px;font-weight:600}.coding-launch small{display:block;font-size:10px;font-weight:400;color:#9a80b1;margin-top:5px}.coding-launch>b{margin-left:auto;font-weight:400;font-size:25px}.coding-launch:hover{transform:translateY(-3px);box-shadow:0 12px 28px #33204e44}@media(max-width:640px){.learning-entry-bar{flex-direction:column;align-items:stretch;gap:12px}.learning-entry-bar>span{font-size:11px}.coding-launch{min-width:0;width:100%}}
.course-enter-active{transition:opacity 420ms ease,transform 420ms cubic-bezier(.16,1,.3,1);transition-delay:var(--course-delay,0ms)}.course-move{transition:transform 480ms cubic-bezier(.16,1,.3,1)}.course-enter-from{opacity:0;transform:translateY(24px) scale(.97)}.course-leave-active{transition-duration:200ms;z-index:0}.course-cover{border-radius:14px 14px 0 0}.course-card{border-radius:16px}
</style>

<style scoped>
.banner-panel.analysis-panel{background:rgba(255,255,255,.96);border:1px solid #e6dced;color:#584169}.analysis-panel :deep(.learning-analysis){max-height:560px;overflow:auto;padding-right:6px}
</style>

<style scoped>
.chart-stats-note{font-size:11px;color:#e1d4f1;line-height:1.8;padding:0 4px}
</style>
